from flask import Flask, render_template, request
import requests
from itertools import combinations
from pokerlib.enums import Rank, Suit 
from pokerlib import HandParser
import random

# BUGS:
# Fichas do jogador e bots sao globais e valem p todas as salas, o pot também pode acumular em algumas situações
# Fold na ultima rodada não funciona - qualquer ação na ultima rodada é ignorada e conta como check

# TO DO:
# Escolher valor da aposta
# Colocar na tela a ação do bot
# Aparecer na tela quem eh big blind e small blind - tvz
# Pot auxiliar com as apostas da rodada separado do pot principal - tvz




app = Flask(__name__)


salas = [] 
valores = {
            '2': 2, '3': 3, '4': 4, '5': 5,
            '6': 6, '7': 7, '8': 8, '9': 9,
            'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }

@app.route('/')
def index():
    return render_template('index.html')  ############## O arquivo HTML da tela inicial



@app.route('/mesas', methods = ['GET', 'POST']) ################ primeira mudança mudei pra app rout para mesas pois index e a tela inicial estava home


def home(): 
    salas[0].rodada = -1 #
    if request.method == 'POST':
        nome = request.form.get("nome")
        tamanho = request.form.get("tamanho")
        small = request.form.get("small")
        big = request.form.get("big")
        jogador.criar_sala(nome, small, big, bot)

    return render_template('mesas.html', salas=salas, jogador=jogador, bot=bot)


# TEM COISA ERRADA COM O APOSTADOR - sipa
# no geral o sistema de rodadas ta zuado
@app.route('/mesa', methods = ['GET', 'POST'])
def entrarMesa(): 
    if salas[0].rodada == 5 or jogador.estado == -1 or bot.estado == -1:
        salas[0].rodada = -1

    if salas[0].apostador == None or salas[0].call:
        salas[0].rodada += 1 # qnd for fazer p bot apostar tem q mudar isso, tvz jogar la p baixo e dps colocar o apostaBot(), tvz fazer um esquema de so aumentar a rodada se o apostador for None

    print("call -", salas[0].call)
    try:
        print("Apostador -", salas[0].apostador.nome)
    except:
        print("Apostador - None")

    # if salas[0].rodada == 0: # iniciar rodada
    #     salas[0].iniciar_rodada() 
    #     print("rodada",salas[0].rodada)
    #     salas[0].rodada+=1
    if salas[0].rodada == 0: # iniciar rodada
        salas[0].iniciar_rodada() 
        print("rodada",salas[0].rodada)
      
        if jogador.e_bb: # so p cubrir o big blind
            salas[0].apostaBot(salas[0].small_blind, jogador)
            
        salas[0].rodada+=1

    elif salas[0].rodada == 1:
        # if jogador.e_bb: 
        #     salas[0].apostaBot(0, jogador) # --------------
        #     print("fodasse")
        #     print(jogador.e_bb)
        if request.method == "POST":
            escolha = request.form['escolha']
            salas[0].rodada_aposta(0,escolha,jogador, True) # botei 0 pq ta foda
        print("rodada",salas[0].rodada)

    elif salas[0].rodada > 1 and salas[0].rodada < 5: 
        # if jogador.e_bb: 
        #     salas[0].apostaBot(0, jogador) # --------------
        #     print("fodasse")
        #     print(jogador.e_bb)
        if request.method == "POST":
            escolha = request.form['escolha']
            salas[0].rodada_aposta(0,escolha,jogador, False) # botei 0 pq ta foda
        print("rodada",salas[0].rodada)
        

    elif salas[0].rodada == 5: # fim de jogo
        salas[0].final()
        print("rodada",salas[0].rodada)
        print(salas[0].vencedores)

    else:
        print("deu merda")

    if jogador.estado == -1 or bot.estado == -1:
        salas[0].final()
        salas[0].rodada-=1 # gueri gueri

    print("estado", jogador.estado, bot.estado)


    return render_template('mesa.html', sala=salas[0], jogador=jogador, bot=bot)

@app.route('/mesas')
def mesas():
    salas[0].rodada = 0
    return render_template('mesas.html', salas=salas, jogador=jogador)

# ---------------------------------------------------------------------------------------------------------------------------------------------



class Player:
    def __init__(self, nome, chips):
        self.nome = nome
        self.fichas = chips
        self.cards = []
        self.indice_sala = -1 # tem q ser atualizado qnd ele entrar numa sala
        self.estado = 0 # 0 = "na rodada mas não jogou", 1 = "na rodada e ja jogou", -1 = "fora da rodada"
        self.e_bb = False # atributo novo que diz se é bb
        self.e_sb = False # atributo novo que diz se é sb
        self.aposta = 0 # atributo novo


    def criar_sala(self, nome_sala, small_blind, big_blind, bot):
        # quando criar a sala colocar um outro jogador q vai ser o bot, fazer acoes basicas dele
        nova_sala = PokerRoom(nome_sala, 4, small_blind, big_blind)
        nova_sala.adicionar_jogador(bot)
        salas.append(nova_sala)
        self.indice_sala = len(salas) - 1 
        nova_sala.players.append(self) 
        return nova_sala

    def entrar_sala(self, nome_sala):
        for sala in salas:
            if len(sala.players) < sala.seats and sala.nome == nome_sala:
                self.indice_sala = salas.index(sala)
                sala.players.append(self)
                return True
        return False

    def coletar_cartas(self, deck_id):
        url = f"https://deckofcardsapi.com/api/deck/{deck_id}/draw/?count=2"
        self.cards = requests.get(url).json()['cards']

    # função nova
    def print_cartas(self):
        for card in self.cards:
            print(card['code'], end = " ")
        print()

    # função nova
    def aposta_pot(self): # não esta sendo usada, foi na raça msm
        # sala = salas[self.indice_sala] ANTIGO 
        sala = salas[0]
        self.fichas -= self.aposta
        sala.pot += self.aposta
        self.aposta = 0

    # função modificada
    def realizar_acao(self, acao, valor=None): 
        sala = salas[0] # antes era sala = self.indice_sala
        if acao == 'BET':
            sala.apostador = self
            print("Apostador é", sala.apostador.nome)
            self.estado = 1
            self.aposta += valor
        
        elif acao == 'CALL':
            sala.apostador = None
            sala.call = True
            self.estado = 1
            self.aposta = valor
        
        elif acao == 'FOLD':
            self.estado = -1
            self.aposta = 0

        elif acao == 'CHECK':
            self.estado = 1
            self.aposta = 0

        # equivalente a funcao aposta_pot
        self.fichas -= self.aposta
        sala.pot += self.aposta
        self.aposta = 0
        
        return True

    
# ---------------------------------------------------------------------------------------------------------------------------------------------
class PokerRoom:
    def __init__(self, nome, seats, small_blind, big_blind):
        self.nome = nome
        self.seats = seats
        self.big_blind = big_blind
        self.small_blind = small_blind
        self.players = []

        self.rodada = -1 # antes era 0
        self.acabou = False
        self.vencedores = []
        self.lib = {0 : "HIGHCARD", 1: "ONEPAIR", 2:"TWOPAIR",3: "THREEOFAKIND", 4 : "STRAIGHT", 5: "FLUSH", 6: "FULLHOUSE", 7: "FOUROFAKIND", 8: "STRAIGHTFLUSH"}
        self.biblis = {
            'A': Rank.ACE, '2': Rank.TWO, '3': Rank.THREE, 
            '4': Rank.FOUR, '5': Rank.FIVE, '6': Rank.SIX,
            '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
            '0': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN,
            'K': Rank.KING, 'S': Suit.SPADE, 'C':Suit.CLUB, 'H': Suit.HEART, 'D' : Suit.DIAMOND
        }
        self.apostador = None
        self.call = False

        self.deck = requests.get("https://deckofcardsapi.com/api/deck/new/shuffle/?deck_count=1").json()['deck_id']
        self.pot = 0
        self.flop = []
        self.turn = []
        self.river = []

    def adicionar_jogador(self, player):
        if len(self.players) < self.seats:
            self.players.append(player)
            player.coletar_cartas(self.deck)

    def print_flop(self):
        for card in self.flop:
            print(card['code'], end = " ")
        print()

    def print_turn(self):
        print(self.turn[0]['code'])

    def print_river(self):
        print(self.river[0]['code'])

    def print_fichas(self):
        print(f"pot: {self.pot}")
        for player in self.players:
            print(f"{player.nome} ficou {player.fichas}")
        print("\n\n")


    def verificar_ganhadores(self):
        
        cartas_mesa = self.flop + self.turn + self.river
        vetor_resposta = []

        for idx,player in enumerate(self.players):
            all_cards = player.cards + cartas_mesa
            card_strings = [card['code'] for card in all_cards]
            cartas_jogador = HandParser([])
            for card in card_strings:
                carta = [(self.biblis[card[0]],self.biblis[card[1]])]
                cartas_jogador += carta
            vetor_resposta.append((cartas_jogador, player))
        vetor_resposta = sorted(vetor_resposta, reverse=True)
        vencedores = []
        vencedores.append(vetor_resposta[0])
        i = 1
        while vetor_resposta[0][0] == vetor_resposta[i][0]:
            vencedores.append(vetor_resposta[i][0])
            i += 1
        return vencedores

    # função nova
    def verifica_unico_jogador(self):
        jogadores_ativos = [player for player in self.players if player.estado != -1]
        if len(jogadores_ativos) == 1:
            return jogadores_ativos[0]
        return None
    
    def apostaBot(self, valor, player):

        #{0 : "HIGHCARD", 1: "ONEPAIR", 2:"TWOPAIR",3: "THREEOFAKIND", 4 : "STRAIGHT", 5: "FLUSH", 6: "FULLHOUSE", 7: "FOUROFAKIND", 8: "STRAIGHTFLUSH"}
        all_cards = bot.cards + []
        if self.rodada >= 2:
            all_cards += self.flop
        if self.rodada >= 3:
            all_cards += self.turn
        if self.rodada >= 4:
            all_cards += self.river
        
        card_strings = [card['code'] for card in all_cards]
        cartas_bot = HandParser([])
        for card in card_strings:
            carta = [(self.biblis[card[0]],self.biblis[card[1]])]
            cartas_bot += carta
        combo = cartas_bot.handenum
        print("combo:", combo)
        # ver se é bom ou nao o combo, combo é numerico 0 a 8

        chance = random.randrange(1, 11) # 1 a 10

        if self.apostador == player:
            if self.rodada <= 1: # acho q ta errado, as rodadas tao atrasadas
                bot.realizar_acao("CALL", valor)
            elif self.rodada == 2:
                if combo >= 2:
                    bot.realizar_acao("CALL", valor)
                elif combo == 1:
                    if chance >= 5:
                        bot.realizar_acao("CALL", valor)
                    else:
                        bot.realizar_acao("FOLD", valor)
                elif combo == 0:
                    if chance >= 8:
                        bot.realizar_acao("CALL", valor)
                    else:
                        bot.realizar_acao("FOLD", valor)
            elif self.rodada == 3:
                if combo >= 3:
                    bot.realizar_acao("CALL", valor)
                elif combo == 2:
                    if chance >= 2:
                        bot.realizar_acao("CALL", valor)
                    else:
                        bot.realizar_acao("FOLD", valor)
                elif combo == 1:
                    if chance >= 5:
                        bot.realizar_acao("CALL", valor)
                    else:
                        bot.realizar_acao("FOLD", valor)
                elif combo == 0:
                    if chance >= 9:
                        bot.realizar_acao("CALL", valor)
                    else:
                        bot.realizar_acao("FOLD", valor)
            elif self.rodada == 4:
                if combo >= 3:
                    bot.realizar_acao("CALL", valor)
                elif combo == 2:
                    if chance >= 3:
                        bot.realizar_acao("CALL", valor)
                    else:
                        bot.realizar_acao("FOLD", valor)
                elif combo == 1:
                    if chance >= 5:
                        bot.realizar_acao("CALL", valor)
                    else:
                        bot.realizar_acao("FOLD", valor)
                elif combo == 0:
                    bot.realizar_acao("FOLD", valor)
            elif self.rodada == 5: # to meio confuso se isso rola
                if combo >= 3:
                    bot.realizar_acao("CALL", valor)
                elif combo == 2:
                    if chance >= 3:
                        bot.realizar_acao("CALL", valor)
                    else:
                        bot.realizar_acao("FOLD", valor)
                elif combo == 1:
                    if chance >= 5:
                        bot.realizar_acao("CALL", valor)
                    else:
                        bot.realizar_acao("FOLD", valor)
                elif combo == 0:
                    bot.realizar_acao("FOLD", valor)

        else: # logica para aposta do bot
            if self.rodada <= 1: # acho q ta errado, as rodadas tao atrasadas
                bot.realizar_acao("CHECK", valor)
            elif self.rodada == 2:
                if combo >= 5:
                    bot.realizar_acao("BET", valor)
                elif combo == 1:
                    if chance >= 8:
                        bot.realizar_acao("BET", valor)
                    else:
                        bot.realizar_acao("CHECK", valor)
                elif combo == 0:
                    if chance >= 9:
                        bot.realizar_acao("BET", valor)
                    else:
                        bot.realizar_acao("CHECK", valor)
            elif self.rodada == 3:
                if combo >= 3:
                    bot.realizar_acao("BET", valor)
                elif combo == 2:
                    if chance >= 3:
                        bot.realizar_acao("BET", valor)
                    else:
                        bot.realizar_acao("CHECK", valor)
                elif combo == 1:
                    if chance >= 6:
                        bot.realizar_acao("BET", valor)
                    else:
                        bot.realizar_acao("CHECK", valor)
                elif combo == 0:
                    if chance >= 10:
                        bot.realizar_acao("BET", valor)
                    else:
                        bot.realizar_acao("CHECK", valor)
            elif self.rodada == 4:
                if combo >= 3:
                    bot.realizar_acao("BET", valor)
                elif combo == 2:
                    if chance >= 5:
                        bot.realizar_acao("BET", valor)
                    else:
                        bot.realizar_acao("CHECK", valor)
                elif combo == 1:
                    if chance >= 7:
                        bot.realizar_acao("BET", valor)
                    else:
                        bot.realizar_acao("CHECK", valor)
                elif combo == 0:
                    bot.realizar_acao("CHECK", valor)
            elif self.rodada == 5: # to meio confuso se isso rola
                if combo >= 3:
                    bot.realizar_acao("BET", valor)
                elif combo == 2:
                    if chance >= 5:
                        bot.realizar_acao("BET", valor)
                    else:
                        bot.realizar_acao("CHECK", valor)
                elif combo == 1:
                    if chance >= 6:
                        bot.realizar_acao("BET", valor)
                    else:
                        bot.realizar_acao("CHECK", valor)
                elif combo == 0:
                    bot.realizar_acao("CHECK", valor)


    # função nova 
    def rodada_aposta(self,maior,acao,player,inicial): # voltar com algumas coisas do victao antigas, principalmente parte do big e small blind

        player.estado = 0
        self.call = False
        valor = 0

        if acao == "BET":
            #valor = int(input("valor: "))
            valor = self.big_blind # valor padrao de aposta
            player.realizar_acao("BET",valor)
            
            #self.apostaBot(valor, player) # -----------------

            #maior += valor

            # teste (parece correto)
            # aux = maior
            # if player.e_bb and inicial:
            #     aux = maior - self.big_blind
            # if player.e_sb and inicial:
            #     aux = maior - self.small_blind
            # player.realizar_acao("CALL",aux)
            # fim de teste

        elif acao == "CALL":
            #aux = maior
            aux = self.big_blind
            if inicial: # teste
                maior = self.big_blind

            if player.e_bb and inicial:
                aux = maior - self.big_blind
            if player.e_sb and inicial:
                aux = maior - self.small_blind

            print("aux", aux)
            player.realizar_acao("CALL",aux)

        elif acao == "FOLD":
            player.realizar_acao("FOLD")
            self.acabou = True

        elif acao == "CHECK":
            player.realizar_acao("CHECK")
            #bot.realizar_acao("CHECK") # mexer

        # if player.estado != -1: # n saiu
        #     player.estado = 0

        if player.e_sb and player.estado == 1 and self.call == False: # jogador é small blind e ja fez sua ação
            self.apostaBot(valor, player)

        elif player.e_bb and self.call == False: # jogador é big blind e ainda não deu call
            self.apostaBot(valor, player)

        # if self.apostador == None:
        #     self.rodada += 1 

    def iniciar_rodada(self):
        salas[0].flop = requests.get(f"https://deckofcardsapi.com/api/deck/{salas[0].deck}/draw/?count=3").json()['cards']
        salas[0].turn = requests.get(f"https://deckofcardsapi.com/api/deck/{salas[0].deck}/draw/?count=1").json()['cards']
        salas[0].river = requests.get(f"https://deckofcardsapi.com/api/deck/{salas[0].deck}/draw/?count=1").json()['cards']
        # distribui as cartas para cada player e atribui o estado 0 que indica "a jogar"
        for p in range(len(self.players)):
            self.players[p].estado = 0
            self.players[p].coletar_cartas(self.deck)
            self.players[p].print_cartas() 

            self.players[p].e_bb = False
            self.players[p].e_sb = False
            
            # define que o ultimo é o BB
            if p == len(self.players) - 1:
                self.players[p].fichas -= self.big_blind
                self.players[p].e_bb = True 
                self.pot += self.big_blind
                print(f"BB: {self.players[p].nome}\n\n")
                
                self.apostador = self.players[p] # novo

            # define que o penultimo é o SB
            elif p == len(self.players) - 2:
                self.players[p].fichas -= self.small_blind
                self.players[p].e_sb = True
                self.pot += self.small_blind
                print(f"SB: {self.players[p].nome}\n\n")

            
    
        # site que eu vi legal pra "roubar o css" == https://www.247freepoker.com/ (◠‿◠)

    # def preFlop(self):
    #     # PRE-FLOP
    #     self.print_fichas()
    #     #self.rodada_aposta(self.big_blind,True)
    #     self.print_fichas()

    #     vencedor = self.verifica_unico_jogador()
    #     if vencedor is not None:
    #         print(f"O vencedor é {vencedor.nome}!")
    #         return vencedor
        
    

    def final(self):

        if jogador.estado == -1:
            bot.fichas += self.pot
            #jogador.estado = 0
        elif bot.estado == -1:
            jogador.fichas += self.pot
            #bot.estado = 0
        else:
            self.vencedores = self.verificar_ganhadores()
        
            for winner in self.vencedores:
                print(f"VENCEDOR FOI {winner[1].nome} tendo {self.lib[winner[0].handenum]}\n\n")

            self.vencedores[0][1].fichas += self.pot

        self.pot = 0
        self.print_fichas()

        # troca o BB e SB
        BB = self.players.pop(0)
        self.players.append(BB)

        # retorna as cartas para o deck
        requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck}/return/")
        requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck}/shuffle/") 

        self.apostador = None

# ------------------------------------------------------------------------------------------------------------------------------------------------

def listar_partidas():
    if not salas:
        print("Nenhuma partida disponível no momento.")
        return []
    else:
        print("Partidas disponíveis:")
        for idx, sala in enumerate(salas):
            print(f"{idx}. Nome: {sala.nome}, Cadeiras: {sala.seats}, Blinds: {sala.big_blind}/{sala.small_blind}, Jogadores: {len(sala.players)}")
        return salas


def iniciar_partida(indice_sala):
    try:
        sala = salas[indice_sala]
        if len(sala.players) > 1:
            sala.start()
            print(f"Partida '{sala.nome}' iniciada com sucesso!")
            return True
        else:
            print(f"Partida '{sala.nome}' não iniciada! Precisa de mais jogadores.")
            return False
    except IndexError:
        print(f"Erro: Não existe uma partida no índice {indice_sala}.")
        return False

    



jogador = Player('victor', 1000)
bot = Player("bot", 1000)
jogador.criar_sala('sala1', 5, 10, bot)
jogador.criar_sala('sala2', 10, 20, bot)



if __name__ == '__main__':
    app.run(debug=True)