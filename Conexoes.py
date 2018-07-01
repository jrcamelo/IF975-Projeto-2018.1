import socket
import http.server
import socketserver
import json


#Comunicador é o que controla a primeira questão
#É usado antes do usuário logar
class Comunicador():

    #O tipo da conexão é informada logo ao criar o objeto
    def __init__(self, ip, rand, tipo):
        self.ip = ip
        self.rand = rand
        self.tipo = tipo
        

    #As portas são diferentes para cada tipo de conexão
    #Para evitar problemas e testar ainda mais portas
    #É usado um número aleatório que vai de 1 a 1000
    #Isso ajuda principalmente contra conflito no bind
    def EscolherPorta(self):      
        if self.tipo == "TCP":
            self.porta = 5000 + self.rand
        elif self.tipo == "UDP":
            self.porta = 6000 + self.rand
        elif self.tipo == "HTTP":
            self.porta = 8000 + self.rand
        else:
            return ""
        return str(self.porta)

    #Inicia a comunicação
    def Comunicar(self):
        if self.tipo == "TCP":
            self.UsarTCP()
        elif self.tipo == "UDP":
            self.UsarUDP()
        elif self.tipo == "HTTP":
            self.UsarHTTP()



    def UsarTCP(self):
        #Cria o socket               IPV4             TCP            
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Faz o bind com o ip e porta
        tcp.bind((self.ip, self.porta))
        #E escuta somente um usuário
        tcp.listen(1)

        conn, usuario = tcp.accept()
        ident = usuario[0] + ":" + str(usuario[1])
        print(ident + " (TCP) - Conectado")

        #Faz uma comunicação simples onde devolve o inverso do que foi recebido
        #Caso seja um número, devolve o seu reverso, que é o x(-1)
        #Termina ao receber uma mensagem vazia
        while True:
            msg = conn.recv(1024)
            print (ident + " (TCP) - " + msg.decode('utf-8'))
            if not msg:
                break

            if msg.decode('utf-8').isdigit():
                msg = int(msg.decode('utf-8')) * -1
                msg = str(msg).encode('utf-8')
            else:
                msg = msg.decode('utf-8')[::-1].encode('utf-8')
                
            conn.send(msg)
            
        print(ident + " (TCP) - Desconectado")
        conn.close()

            

    #Funciona da mesma forma do UsarTCP
    #Mas sem a parte de aceitar a conexão
    #Escutando todas mensagens mandadas no endereço
    def UsarUDP(self):
        #Cria o socket              IPV4            UDP
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        udp.bind((self.ip, self.porta))
        
        while True:
            msg, usuario = udp.recvfrom(1024)
            ident = usuario[0] + ":" + str(usuario[1])
            print (ident + " (UDP) - " + msg.decode('utf-8'))
            if not msg:
                break

            if msg.decode('utf-8').isdigit():
                msg = int(msg.decode('utf-8')) * -1
                msg = str(msg).encode('utf-8')
            else:
                msg = msg.decode('utf-8')[::-1].encode('utf-8')
            
            udp.sendto(msg, usuario)
            
        print(ident + " (UDP) - Desconectado")
        udp.close()

        

    def UsarHTTP(self):
        global continuar
        continuar = True

        #Cria um servidor que escuta requisições
        #O único comando aceitável é o POST
        http = socketserver.TCPServer((self.ip, self.porta), POST_Handler)
        print('Iniciando Servidor HTTP em ' + str(self.porta))

        #E fica em um loop de tratamento de requisições
        #Até que é parado no próprio método de tratamento usando uma variável global
        while continuar:
            http.handle_request()
        print("Servidor HTTP em "+ str(self.porta) + " foi fechado")
        


class POST_Handler(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        global continuar

        #Pega a mensagem
        content_len = int(self.headers.get_all('content-length')[0])
        post_body = self.rfile.read(content_len)
        #Envia o OK
        self.send_response(200)
        self.end_headers()

        #Decodifica a mensagem, que vem em formato de JSON (texto)
        data = json.loads(post_body.decode())
        msg = data['msg']
        print(msg)

        #Ao invés de vazio, aqui o comando que termina é o KILL
        #Que muda a variável global do while para False
        if msg == "KILL":
            continuar = False
            return
            
        if msg.isdigit():
            msg = int(msg) * -1
            msg = str(msg)
        else:
            msg = msg[::-1]

        #Envia a resposta
        self.wfile.write(msg.encode())
