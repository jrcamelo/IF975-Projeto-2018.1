import socket
from _thread import start_new_thread
import time
import base64
import json
import os



from Server.Interface import Usuario
from Jogo import LittleZero

class Servidor():

    def __init__(self, ip, porta):
        self.ip = ip
        self.porta = porta
        
        #Dicionário de usuários registrados
        self.Database = {}
        self.OnlineUsers = {}

        #Servidor para a terceira questão
        self.Lobby = LittleZero()
        
        self.ServerStart(ip, porta)
        

    def ServerStart(self, ip, porta):
        #Popula o dicionário para se preparar para logins
        self.Database = self.ReadDatabase()
        
        #Cria o socket               IPV4                TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #Define o IP e a porta
        sock.bind((ip, porta))
        print("Servidor iniciado em " + str(ip) + ":" + str(porta))

        #Máximo de usuários ao mesmo tempo
        sock.listen(10)

        #Inicia o servidor do Jogo
        start_new_thread(self.Lobby.Iniciar, (ip, porta+1))
        
        #Aceita novos usuários e cria threads para eles
        while True:
            conn, addr = sock.accept()
            #addr[0] é o IP e addr[1] é a porta
            print("Conexão de " + str(addr[0]) + ":" + str(addr[1]))
            out = "Olá, bem vindo ao Servidor!"
            conn.sendall(out.encode('utf-8'))

            #Adiciona o usuário no dicionário, sem nome
            self.OnlineUsers[addr] = ""

            #Inicia a Thread
            start_new_thread(self.KeepClient, (conn, addr))

        sock.close


    def ReadDatabase(self):
        if not os.path.isfile(os.getcwd() + "/Server/database"):
            self.WriteDatabase()
        with open(os.getcwd() + "/Server/database") as file:
            return json.load(file)
    def WriteDatabase(self):
        with open(os.getcwd() + "/Server/database", 'w') as file:            
            json.dump(self.Database, file, indent=8)
        

    #Método de tratamento dos clientes
    def KeepClient(self, conn, addr):
        ident = str(addr[0]) + ":" + str(addr[1])
        
        #Cria a interface do usuário
        client = Usuario(self, conn)
        
        user = ""
        while True:
            try:
                #Receber 1024 bytes por TCP
                msg = conn.recv(1024).decode()
                if not msg:
                    break
                print(ident + " - " + msg)
                if msg == "DESCONECTAR":
                    break

                #Executa o comando recebido pelo cliente
                #Caso o método devolva alguma string
                #Ela é mandada para o cliente, pois pode ser um erro
                #Ou uma mensagem simples que não foi tratada
                result = client.Executar(msg)
                if result != None and result:
                    if result != "OK":
                        print(result)
                    conn.send(result.encode())

                #Checa se o usuário já tem um nome e coloca-o na lista de online
                if not user:
                    user = client.user
                    if user:
                        self.OnlineUsers[addr] = user
                        ident += " (" + user + ")"

            #Mesmo que aconteça algo, como uma desconexão repentina
            #O servidor faz questão de remover o usuário da lista dos Online
            #E também o remove do Servidor da terceira questão
            except ConnectionAbortedError as e:
                print(ident + " encerrou a conexão subitamente!")
                break
            except ConnectionResetError as e:
                print(ident + " teve a conexão encerrada!")
                break
            #Trata qualquer outra exceção
            #Útil por não parar o servidor por algum erro em um usuário
            except BaseException as e:
                print(ident + " causou algum problema!")
                print(str(e))
                break

        #Sempre fecha, mesmo com interrupções
        conn.close()
        self.OnlineUsers.pop(addr)
        self.Lobby.RemoverJogador(user)


    #Método de comunicação bastante utilizado
    def SendMessage(self, conn, msg, err):
        if err:
            msg = err
        conn.sendall(msg.encode())


    def Login(self, tcp, user):
        if not user in self.Database.keys():            
            time.sleep(0.2)
            return "", "<USUARIO NAO EXISTE>"
        else:

            #Checa na lista de usuários online se ele já esta logado
            #O que proibe um usuário logado em dois clientes diferentes
            u, err = self.GetAddr(user)
            if u:
                return "", "<USUÁRIO JÁ ESTA LOGADO!>"
            
            tcp.send(user.upper().encode())
            tries = 0
            while True:
                tries += 1
                p = tcp.recv(1024).decode()

                #Caso o usuário interrompa, volta para o menu
                if p == "CANCEL":
                    return "", ""

                #Desencripta a senha recebida
                p = self.Decrypt(p)
                time.sleep(0.2)

                #Caso o usuário erre a senha, permite-o continuar tentando
                if p != self.Database[user]['P']:
                    tcp.send("<SENHA INCORRETA>".encode())

                else:
                    #Manda duas mensagens
                    #Timer faz com que elas não se misturem
                    tcp.send("SENHA CORRETA".encode())
                    
                    time.sleep(0.5)                    
                    name = "Usuario"
                    
                    tcp.send(name.encode('utf-8'))
                    return name, ""
                
                if tries == 5:
                    print("Muitas tentativas inválidas de login em " + user)
                    tries = 0


    def CreateUser(self, tcp, user):
        if user in self.Database.keys():
            tcp.send("<USUARIO JA EXISTE>".encode())
            return False
        else:
            #Usuário válido
            tcp.send("OK".encode())

            name = tcp.recv(1024).decode()
            if name == "CANCEL":
                return False
            #Avisa que recebeu sem problemas
            tcp.send("OK".encode())

            #Recebe a senha encriptada
            p = tcp.recv(1024).decode()
            if p == "CANCEL":
                return False

            p = self.Decrypt(p)

            #Avisa que registrou
            self.Database[user] = {"N": name, "P": p}
            print(user + " REGISTRADO!")
            self.WriteDatabase()    

            tcp.send("OK".encode())       


    #Decriptografria simples com Base64
    #A chave é simétrica, então o cliente tem uma igual
    #Não é tão seguro, mas ajuda
    def Decrypt(self, enc):
        key = "IF975 - Projeto de Redes"
        result = []
        enc = base64.urlsafe_b64decode(enc).decode()
        for i in range(len(enc)):
            key_c = key[i % len(key)]
            result_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
            result.append(result_c)
        return "".join(result)


    #Faz uma lista de usuários online
    def ShowUsers(self, user):
        others = []
        for addr in self.OnlineUsers:
             other = self.OnlineUsers[addr]
             if other and not other == user:
                 others.append(other)
        return others

    #Procura um usuário na lista de usuários online
    def GetAddr(self, user):
        for addr in self.OnlineUsers:
             if self.OnlineUsers[addr] == user:
                 ip = str(addr[0])
                 porta = str(addr[1])
                 return ip + ":" + porta, ""
        return "", "<Usuário não encontrado>"
                 
        

    #Envia o arquivo em blocos de 1024 bytes
    #Antes de começar, informa o tamanho do arquivo
    #E quando termina, avisa que já terminou
    def SendFile(self, conn, user, path, size):
        print("Enviando arquivo para " + user)
        conn.send(str(size).encode())        
        
        file = open(path, 'rb')
        f = file.read(1024)
        while f:
            conn.send(f)
            f = file.read(1024)
        file.close()
        time.sleep(0.2)
        conn.send(b"<FIM DE ARQUIVO>")
        print("Arquivo de " + str(size) + "Bs enviado para " + user)


    #Saber quando o arquivo terminou de ser enviado foi um grande problema
    #Então são feitas duas checagens para o fim do arquivo
    #Uma é pela quantidade de dados recebida
    #Caso seja igual ou maior que a informada no começo, termina a transferência
    #E a segunda é uma mensagem de FIM DE ARQUIVO
    #Que pode ser recebida pelo método KeepClient sem problemas
    def GetFile(self, conn, user, path, size):
        conn.send(b"OK")
        print("Recebendo arquivo de " + user)
        err = False
        written = 0
        try:
            with open(path, 'wb') as file:
                while True:
                    dados = conn.recv(1024)
                    if not dados:
                        err = True
                        break
                    if dados == b"<FIM DE ARQUIVO>":
                        #OK
                        break                
                    file.write(dados)
                    written += 1024
                    if written >= size:
                        #OK
                        break
                        
        except ConnectionError as e:
            print("ERRO!")
            return e
        if err:
            return "<Ocorreu um erro na transmissão!>"
        
        print("Arquivo recebido de " + user)
        conn.send(b"OK")        
        




################################################          
if __name__ == '__main__':
    with open("ip.txt", 'r') as arquivo:
        ip = arquivo.readline()
    porta = 9750

    Server = Servidor(ip, porta)
             




    

