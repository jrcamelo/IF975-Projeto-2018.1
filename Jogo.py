import socket
import time


class LittleZero():

    def __init__(self):
        self.jogadores = []

    #Inicia a espera para começar o jogo
    def Iniciar(self, ip, porta):
        self.ip = ""
        self.porta = porta

        quantidade = 5
        while True:
            time.sleep(2)

            #Se não tiver jogadores, espera 10 segundos para checar de novo
            if not self.jogadores:
                time.sleep(8)
                    
            #Inicia o jogo se houver um bom número de jogadores
            elif len(self.jogadores) >= quantidade:
                self.Jogar()
                time.sleep(3)            

            #Se houverem 2 jogadores, espera 10 segundos por outros jogadores
            elif len(self.jogadores) > 1:                
                quantidade -= 1
                if quantidade == 1:
                    quantidade = 5
                    

    #Devolve uma string com a lista de jogadores em espera
    def ListarJogadores(self):
        msg = "No Lobby: "
        nomes = []
        for j in self.jogadores:
            nomes.append(j[0])
        if not nomes:
            return msg + "NINGUÉM :("
        return msg + ", ".join(nomes)

    #Chamado pela Interface, adiciona um jogador na espera
    def AdicionarJogador(self, nome, numero):
        if self.JaJogando(nome):
            return "<JOGADOR JÁ ESTÁ NO LOBBY>"
        jogador = (nome, numero)
        self.jogadores.append(jogador)
        return self.porta

    #Chamado pelo servidor quando um Cliente desconecta
    def RemoverJogador(self, nome):
        for i in range(len(self.jogadores)):
            if self.jogadores[i][0] == nome:
                self.jogadores.pop(i)
                return

    #Impede que um jogador tente entrar novamente no mesmo jogo
    def JaJogando(self, nome):        
        for i in range(len(self.jogadores)):
            if self.jogadores[i][0] == nome:
                return True
        return False


    def Jogar(self):

        #Processa o jogo e vê quem ganhou
        #####
        soma = 0
        texto = "\n[RESULTADO DO ZERINHO OU UM]\n"
        qtd = len(self.jogadores)
        
        for i in range(qtd):
            nome, numero = self.jogadores[i]
            texto += nome + " -> " + str(numero) + "\n"
            soma += numero

        texto += "\nSOMA = " + str(soma)

        v = soma % qtd
        vencedor = self.jogadores[v][0]

        texto += "\n\n\nO VENCEDOR FOI " + vencedor + "!!!"
        #####

        #Informa a todos sobre o resultado
        self.EnviarVencedor(texto)

        #Limpa o saguão, tirando todos jogadores
        self.jogadores.clear()


    def EnviarVencedor(self, msg):
        #Esse e o grupo que receberá a mensagem
        MCAST_GRP = '224.1.1.1'
        #E essa é a porta
        MCAST_PORT = self.porta

        #Cria o socket              IPV4                UDP
        multi = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        #IPPROTO_UDP serve como um checksum para alguns SOs, como o Linux   ^

        #Deixa um TTL de 2 para o pacote
        multi.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        #Então finalmente codifica a mensagem e envia
        multi.sendto(msg.encode(), (MCAST_GRP, MCAST_PORT))




