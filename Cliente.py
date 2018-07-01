import socket
import os
import time
import base64

import struct
import sys
from _thread import start_new_thread

import http.client, urllib.parse, json


def Iniciar():    
    global ip
    global porta
    global tcp
    global user
    global welcome
    
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect((ip, porta))

    welcome = tcp.recv(1024).decode()

    #########
    while True:
        LimparTela()
        print(welcome + "\n")

        if not user:
            MostrarLogin()
        else:

            print("1. EXPLORAR")
            print("2. CRIAR PASTA")
            print("3. FAZER UPLOAD")
            print("4. FAZER DOWNLOAD")
            print("5. MOVER ARQUIVO")
            print("6. MOVER PASTA")
            print("7. DELETAR ARQUIVO")
            print("8. DELETAR PASTA")
            print("9. OUTROS USUÁRIOS")
            print("0. DESCONECTAR")
            
            opcoes = {
                "1": Explorar,
                "2": CriarPasta,
                "3": FazerUpload,
                "4": FazerDownload,
                "5": MoverArquivo,
                "6": MoverPasta,
                "7": DeletarArquivo,
                "8": DeletarPasta,
                "9": OutrosUsers,
                "0": Desconectar
            }
            
            metodo = ""
            while not metodo:
                escolha = input("\nQual ação deseja executar?\n")
                metodo = opcoes.get(escolha, "")
            metodo()

            time.sleep(0.2)
    ######
    Desconectar()


def MostrarLogin():
    print("Você não está logado, o que deseja fazer?\
          \nFavor digitar um dos números\n\n")
    print("1. LOGIN")
    print("2. CRIAR CONTA")
    print("3. TESTAR CONEXÕES")
    print("4. SAIR\n\n")

    while True:
        acao = input(">>>")

        if acao == '1':
            Login()
            break
        if acao == '2':
            Registrar()
            break
        if acao == '3':
            OutrasConexoes()
            break
        if acao == '4':
            print("Adeus! :(")
            Desconectar()
            exit()


def Login():
    global tcp
    global user
    
    while True:
        LimparTela()        
        if user:
            break
        
        u = input("Digite o seu Login:\n")        
        if not u:
            break        
        if Valido(u):
            time.sleep(0.5)
            msg = "LOGIN::<" + u + ">"
            tcp.send(msg.encode('utf-8'))

            resp = tcp.recv(1024).decode()
            if resp != u.upper():
                #Pode ser que o User não exista
                input(resp)
                break
                
            else:                
                while True:
                    time.sleep(0.2)
                    s = input("\nDigite a sua senha:\n")
                    if not s:
                        tcp.send("CANCEL".encode())
                        break
                    
                    tcp.send(Criptografar(s).encode('utf-8'))

                    resp = tcp.recv(1024).decode()
                    if resp == "SENHA CORRETA":                        
                        user = tcp.recv(1024).decode()
                        input("\nLOGIN REALIZADO COM SUCESSO")
                        break
                    else:
                        input(resp)
                        

def Registrar():
    global tcp

    cont = False
    while True:
        LimparTela()
        
        u = input("Digite o Login:\n")        
        if not u:
            break        
        if Valido(u):
            msg = "REGISTER::<" + u + ">"
            tcp.send(msg.encode('utf-8'))

            resp = tcp.recv(1024).decode()
            if resp != "OK":
                #Pode ser que o User já exista
                input(resp)
                break

            n = input("Digite o Nome:\n")
            if not n:                
                tcp.send("CANCEL".encode())
                break            
            tcp.send(n.encode())
            
            resp = tcp.recv(1024).decode()
            if resp != "OK":
                #Pode ter ocorrido algum erro
                input(resp)
                break            
            cont = True
            break
        
    if cont:
        while True:
            p = input("Digite a Senha:\n")
            if not p:                
                tcp.send("CANCEL".encode())
                break
            if len(p) < 5:
                print("<Senha precisa ter pelo menos 5 digitos>")
            else:
                p = Criptografar(p)
                tcp.send(p.encode('utf-8'))

                resp = tcp.recv(1024).decode()
                if resp == "OK":
                    input("<Conta criada com sucesso!>")
                else: print(resp)
                break


def Explorar(shared=False):
    atual = ""
    err = ""
    msg = "LS::<>"
    if shared:
        msg += "::SHARED"
    tcp.send(msg.encode())
    
    pasta = tcp.recv(1024).decode()

    while True:
        LimparTela()
        if "<PASTA VAZIA>" in pasta:
            pasta += "\n        .-.\n        |.|\n      /)|`|(\ \n     (.(|'|)`)    "
            pasta += "            \n  ~~~~`\`'./'~~~~~~~~~~~~~~~~~~~~~\n        |.| "
            pasta += "         ~~\n        |`|                       \n       ,|'|.      (_)"
            pasta += '          ~~\n        "' + "'" + '"        \..\ \n             ~~     ^~^\n'

        print(pasta)
        print("\n" + err)
        err = ""

        goto = input("Ir para:\n")
        if not goto:
            if atual == "":
                break
            else:
                goto = ".."

        if not Valido(goto):
            resp = "<Caracteres inválidos>"
            
        else:
            if not atual.startswith("/"):
                atual = "/" + atual
            if atual.endswith("/"):
                caminho = atual + goto
            else:
                caminho = atual + "/" + goto

            msg = "LS::<" + caminho + ">"
            if shared:
                msg += "::SHARED"
            tcp.send(msg.encode())
            
            resp = tcp.recv(1024).decode()
            
            if resp.startswith("<"):
                err = resp
                
            elif resp.startswith("["):
                print("\n\n" + resp)
                if input("Caso deseje fazer DOWNLOAD digite " + '"SIM"\n').upper() == "SIM":
                    if atual == "/":
                        atual = ""
                    FazerDownload(atual, goto, shared)
                    
            else: 
                pasta = resp
                atual = pasta.split("\n")[0]
                

def CriarPasta():
    LimparTela()
    print("Os caminhos são no formato /pasta/pasta")
    print("A raíz é simplesmente um espaço vazio\n")
    caminho = input("Digite o caminho onde a nova pasta será feita:\n")
    while True:
        nome = input("\nDigite o nome da nova pasta:\n")
        if Valido(nome):
            if not "." in nome:
                break
        if not nome:
            return
    msg = "MKDIR::<" + caminho + ">::" + nome
    tcp.send(msg.encode())
    resp = tcp.recv(1024).decode()
    if resp == "OK":
        resp = "Pasta criada com sucesso!"        
    input("\n" + resp)
    

def FazerUpload():
    LimparTela()

    caminho = input("Digite o caminho do arquivo que deseja fazer upload\n")
    if not caminho:
        return
    elif not os.path.isfile(caminho):
        input("Arquivo não encontrado")
        return
    
    tamanho = str(os.path.getsize(caminho))
    
    destino = input("\nDigite onde deseja colocar o arquivo, no formato /pasta/pasta\n")

    while True:
        nome = input("\nDigite o nome do arquivo na pasta\n")
        if nome and Valido(nome):
            break
        elif not nome:
            return        
        else:
            print("<Nome inválido>\n")    

    print("\n\nFazer upload de " + str(tamanho) + "Bs?")
    if input('Caso deseje CANCELAR, digite "NAO"\n').upper() == "NAO":
        return        
    print("\n"*10)
    print("Contatando servidor...")

    put = ""
    msg = "POST::<" + destino +">::" + nome + "::" + tamanho    
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if resp != "OK":
        input(resp)
        if resp == "<Arquivo já existe!>":
            subst = input('\nDIGITE "SIM" CASO DESEJE SUBSTITUIR O ARQUIVO\n')
            if subst.upper() == "SIM":
                put = "::PUT"
            else:
                return
        else:
            return
    if put:       
        msg = "POST::<" + destino +">::" + nome + "::" + tamanho + put
        tcp.send(msg.encode())
        time.sleep(1)
        resp = tcp.recv(1024).decode()
    
    print("Enviando arquivo...")
    arquivo = open(caminho, 'rb')
    arq = arquivo.read(1024)
    while arq:
        tcp.send(arq)
        arq = arquivo.read(1024)    
    time.sleep(1)
    tcp.send(b"<FIM DE ARQUIVO>")      
    arquivo.close()
    print("Arquivo enviado...")

    resp = tcp.recv(1024).decode()
    if resp == "OK":
        input("Servidor recebeu com sucesso!")
    else:
        input(resp)


def FazerDownload(caminho = "", nome = "", shared = False):
    LimparTela()

    if not nome:
        caminho = input("Digite a pasta do arquivo, no formato /pasta/pasta\n")

        while True:
            nome = input("Digite o nome do arquivo que deseja fazer o download\n")
            if not nome:
                return
            if Valido(nome):
                break

    msg = "GET::<" + caminho + ">::" + nome
    if shared:
        msg += "::SHARED"
    print("Contatando servidor...\n")
    tcp.send(msg.encode())
    
    resp = tcp.recv(1024).decode()
    if resp.isdigit():
        tamanho = int(resp)
    else:
        input(resp)
        return

    print("\n\nRecebendo arquivo...")
    print("Arquivo tem "+ str(tamanho) + "Bs")
    try:
        with open(nome, 'wb') as arquivo:
            escrito = 0
            while True:
                dados = tcp.recv(1024)
                if not dados:
                    break
                if dados == b"<FIM DE ARQUIVOS>":
                    #OK
                    break
                arquivo.write(dados)
                escrito += 1024
                if escrito >= tamanho:
                    #OK
                    tcp.recv(1024)
                    break
        input("Arquivo recebido!")
    except:        
        #Termina de ouvir o servidor
        while dados:
            dados = tcp.recv(1024)
        print("<OCORREU ALGUM ERRO>")
        
    
def MoverArquivo():
    LimparTela()

    caminho = input("Digite a pasta do arquivo, no formato /pasta/pasta\n")
    
    while True:
        nome = input("Digite o nome do arquivo que deseja mover\n")
        if not nome:
            return
        if Valido(nome):
            break

    #Check devolve o tamanho do arquivo, mas serve como um OK    msg = "CHECK::<" + caminho + ">::" + nome
    print("\n\nContatando servidor...")
    
    msg = "CHECK::<" + caminho + ">::" + nome
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if not resp.isdigit():
        input(resp)
        return

    destino = input("\nDigite onde deseja colocar o arquivo, no formato /pasta/pasta\
        \nDigite um " + '"."' + " para manter o caminho anterior\n")
    if destino == ".":
        destino = caminho

    while True:
        novoNome = input("\nDigite o novo nome do arquivo\
        \nDeixe em branco para manter o nome anterior\n")
        if Valido(novoNome):
            break
        if not novoNome:
            novoNome = nome
            if destino == caminho:
                input("Ação redundante :)")
                return
            break
        else:
            print("<Nome inválido>\n")

    #Check com UP no fim vê se o caminho é válido para um upload
    msg = "CHECK::<" + destino + ">::" + novoNome + "::UP"
    tcp.send(msg.encode())

    put = ""
    resp = tcp.recv(1024).decode()
    if resp != "OK":
        input(resp)

        if resp == "<Arquivo já existe!>":
            subst = input('\nDIGITE "SIM" CASO DESEJE SUBSTITUIR O ARQUIVO\n')
            if subst.upper() != "SIM":
                return
        else:
            return
            
    msg = "MOVE::<" + caminho + ">::" + nome
    msg += "::<" + destino + ">::" + novoNome
    print("\n\nContatando servidor...")
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if resp == "OK":
        input("\nArquivo movido com sucesso!")
    else:
        input(resp)


def MoverPasta():
    LimparTela()

    caminho = input("Digite o caminho de onde está a pasta que deseja mover, no formato /pasta/pasta\n")
    
    while True:
        nome = input("Digite o nome da pasta que deseja mover\n")
        if not nome:
            return
        if Valido(nome):
            break

    #Check devolve o tamanho do arquivo, mas serve como um OK    msg = "CHECK::<" + caminho + ">::" + nome
    print("\n\nContatando servidor...")
    
    msg = "CHECKDIR::<" + caminho + ">::" + nome
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if not resp == "OK":
        input(resp)
        return

    destino = input("\nDigite onde deseja colocar a pasta, no formato /pasta/pasta\
        \nDigite um " + '"."' + " para manter o caminho anterior\n")
    if destino == ".":
        destino = caminho

    while True:
        novoNome = input("\nDigite o novo nome da pasta\
        \nDeixe em branco para manter o nome anterior\n")
        if Valido(novoNome):
            break
        if not novoNome:
            novoNome = nome
            if destino == caminho:
                input("Ação redundante :)")
                return
            break
        else:
            print("<Nome inválido>\n")

    #Check com UP no fim vê se o caminho é válido para um upload
    msg = "CHECKDIR::<" + destino + ">::" + novoNome + "::UP"
    tcp.send(msg.encode())

    put = ""
    resp = tcp.recv(1024).decode()
    if resp != "OK":
        input(resp)
        return
            
    msg = "MOVEDIR::<" + caminho + ">::" + nome + "::<" + destino + ">::" + novoNome
    
    print("\n\nContatando servidor...")
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if resp == "OK":
        input("\nPasta movida com sucesso!")
    else:
        input(resp)
        

def DeletarArquivo():
    LimparTela()

    caminho = input("Digite a pasta do arquivo, no formato /pasta/pasta\n")
    
    while True:
        nome = input("Digite o nome do arquivo que deseja deletar\n")
        if not nome:
            return
        if Valido(nome):
            break

    msg = "CHECK::<" + caminho + ">::" + nome
    print("\n\nContatando servidor...")
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if not resp.isdigit():
        input(resp)
        return
    tamanho = int(resp)

    print("\n"*10)
    sim = input("Para DELETAR o " + nome + " que tem " + str(tamanho) + 'Bs, digite "SIM"\n')
    if not sim.upper():
        return

    msg = "DELETE::<" + caminho + ">::" + nome
    print("\n\nContatando servidor...")
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if resp == "OK":
        input("\nArquivo deletado com sucesso!")
    else:
        input(resp)

    
def DeletarPasta():
    LimparTela()

    caminho = input("Digite a pasta que deseja deletar, no formato /pasta/pastadeletar\n")
    if not caminho:
        return

    print("\n"*10)
    sim = input("Para DELETAR a pasta e TUDO que há nela, digite " + '"SIM"\n')
    if not sim.upper():
        return

    msg = "DELDIR::<" + caminho + ">"
    print("\n\nContatando servidor...")
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if resp == "OK":
        input("\nPasta deletada com sucesso!")
    else:
        input(resp)


def OutrosUsers():
    while True:
        LimparTela()
        
        print("1. ACESSAR DATABASE COMPARTILHADO")
        print("2. LISTAR USUÁRIOS ONLINE")
        print("3. COMPARTILHAR ARQUIVO")
        print("4. COMPARTILHAR PASTA")
        print("5. JOGAR ZERINHO OU UM")
        print("0. VOLTAR PARA MENU PRINCIPAL")
        
        opcoes = {
            "1": AcessarCompart,
            "2": ListarOnline,
            "3": CompartArquivo,
            "4": CompartPasta,
            "5": Jogar
        }
        
        metodo = ""
        while not metodo:
            escolha = input("\nQual ação deseja executar?\n")
            if escolha == "0":
                break
            metodo = opcoes.get(escolha, "")
            
        if not metodo:
            break
        
        metodo()
        time.sleep(0.2)


def AcessarCompart():
    LimparTela()

    outro = input("Digite o nome do usuário que deseja acessar:\n")
    if not outro:
        return
    
    msg = "LOAD::" + outro
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if resp != "OK":
        input(resp)
        return
    
    time.sleep(0.2)
    Explorar(True)



def ListarOnline():
    LimparTela()    
    print("USUÁRIOS ONLINE\n")
    
    msg = "OTHERS::LIST"
    tcp.send(msg.encode())    
    resp = tcp.recv(1024).decode()
    input(resp)


def CompartArquivo():
    LimparTela()

    caminho = input("Digite o caminho do arquivo que deseja compartilhar\n")

    while True:
        nome = input("Digite o nome do arquivo que deseja compartilhar\n")
        if not nome:
            return
        if Valido(nome):
            break    
    
    msg = "CHECKSHARE::<" + caminho + ">::" + nome
    print("Contatando servidor...\n")
    tcp.send(msg.encode())
    
    resp = tcp.recv(1024).decode()
    if resp.startswith("<"):
        input(resp)
        return

    print("Arquivo atualmente é compartilhado com...")
    print(resp + "\n\n")

    if resp == "[NINGUÉM]":
        shared = []
    else:
        shared = resp.split(" | ")

    shared = CompartInput(shared)
    shared = " | ".join(shared)
    if shared == resp:
        input("Ação redundante :)")
        return

    msg = "SHARE::<" + caminho + ">::" + nome + "::<" + shared + ">"
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if resp == "OK":
        input("\nArquivo compartilhado com sucesso!")
    else:
        input(resp)
    
    
def CompartPasta():
    LimparTela()

    caminho = input("Digite a pasta que deseja compartilhar\n")
    if not caminho:
        if not input("Deseja mesmo compartilhar a raíz? \
                \nDigite" + '"SIM" para confirmar\n').upper() == "SIM":
            return
    
    msg = "CHECKSHARE::<" + caminho + ">"
    print("Contatando servidor...\n")
    tcp.send(msg.encode())
    
    resp = tcp.recv(1024).decode()
    if resp.startswith("<"):
        input(resp)
        return

    print("Pasta atualmente é compartilhada com...")
    print(resp + "\n\n")

    if resp == "[NINGUÉM]":
        shared = []
    else:
        shared = resp.split(" | ")

    shared = CompartInput(shared)
    shared = " | ".join(shared)

    msg = "SHAREDIR::<" + caminho + ">::<" + shared + ">"
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if resp == "OK":
        input("\nPasta compartilhada com sucesso!")
    else:
        input(resp)


def CompartInput(shared):
    print("Digite os nomes dos usuário com quem deseja compartilhar")
    print("Para descompartilhar, digite um usuário com quem já está compartilhado")
    print("Deixe uma linha em branco para terminar")
    
    while True:
        usuario = input("\n>>>")
        if not usuario:
            break
        elif not Valido(usuario):
            print("<Inválido!>\n")
        elif usuario in shared:
            shared.remove(usuario)
        else:
            shared.append(usuario)
            
    return shared


def Jogar():
    print("Contatando servidor...\n\n")
    msg = "LITTLEZERO::Listar"
    tcp.send(msg.encode())
    
    resp = tcp.recv(1024).decode()
    #Se tudo der certo, é a lista de jogadores
    print(resp)

    while True:
        numero = input("\nEscolha um número de 0 a 10 para entrar no Lobby\n")
        if not numero:
            return
        if numero.isdigit():
            if int(numero) >= 0 and int(numero) <= 10:
                break
    msg = "ORONE::" + numero
    tcp.send(msg.encode())

    resp = tcp.recv(1024).decode()
    if resp.startswith("<"):
        input(resp)
        return
    portaLobby = int(resp)

    start_new_thread(EsperarResultado, (portaLobby,))
    print("\nUma Thread foi iniciada, pressione Enter para voltar ao menu")
    input("Quando a partida terminar, o resultado será mostrado")



    

def EsperarResultado(porta):
    global ip

    #Usa a porta dada pelo servidor
    multicast_port  = porta
    #Esse é o grupo que recebe a mensagem
    multicast_group = "224.1.1.1"
    #E esse é o IP da máquina
    interface_ip    = socket.gethostbyname(socket.gethostname())

    try:
        #Cria o socket            IPV4              UDP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM )
        
        #Faz o bind
        #Só pode ter um bind por máquina
        s.bind((interface_ip, multicast_port ))

        #Estrutura a requisição
        mreq = socket.inet_aton(multicast_group) + socket.inet_aton(interface_ip)
        #E configura o socket
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        #Então espera a mensagem
        print("\n\n" + s.recv(1024).decode() + "\n___________________\n")
        input()

    #Caso haja algum erro, ele é tratado
    except BaseException as e:
        print("\n")
        print(str(e))
        print("\n")
        
    
    
#Escolhe o tipo de conexão
#E escuta do servidor qual porta será usada
def OutrasConexoes():
    global tcp
    global ip
    
    LimparTela()
    print("1. TCP")
    print("2. UDP")
    print("3. HTTP")
    print("4. SAIR\n\n")

    while True:
        acao = input(">>>")

        if acao == '1':
            tcp.send(b"TEST::TCP")
            resp = tcp.recv(1024).decode()
            if resp.isdigit():
                TestarTCP((ip, int(resp)))
            break
        
        if acao == '2':
            tcp.send(b"TEST::UDP")
            resp = tcp.recv(1024).decode()
            if resp.isdigit():
                TestarUDP((ip, int(resp)))            
            break
        
        if acao == '3':
            tcp.send(b"TEST::HTTP")
            resp = tcp.recv(1024).decode()
            if resp.isdigit():
                TestarHTTP((ip, int(resp)))            
            break
        
        if acao == '4':
            break


#Cria uma conexão TCP no endereço informado
#É como a usada no método Iniciar
def TestarTCP(endereco):
    LimparTela()
    
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect(endereco)
    ident = endereco[0] + ":" + str(endereco[1])

    print ('Para sair, mande uma mensagem em branco')
    msg = input("Digite uma mensagem:\n>>>")
    tcp.send(msg.encode('utf-8'))

    while msg:
        resp = tcp.recv(1024)
        print (ident + " - " + resp.decode('utf-8'))

        msg = input("\n>>>")
        tcp.send(msg.encode('utf-8'))

    tcp.close()


#Cria uma conexão simples em UDP
#Mais explicações sobre ela no arquivo de Conexoes
def TestarUDP(endereco):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ident = endereco[0] + ":" + str(endereco[1])

    print ('Para sair, mande uma mensagem em branco')
    msg = input("Digite uma mensagem:\n>>>")
    udp.sendto (msg.encode('utf-8'), endereco)

    while msg:
        resp, server = udp.recvfrom(1024)
        print (ident + " >> " + resp.decode('utf-8'))

        msg = input("\n>>>")
        udp.sendto (msg.encode('utf-8'), endereco)

    udp.close()


#Cria uma conexão HTTP
#Que manda Requisições de POST
def TestarHTTP(endereco):

    print ('Para sair, mande uma mensagem em branco')
    msg = input("Digite uma mensagem:\n>>>")
    params = json.dumps({'msg': msg})
    params = json.dumps({'msg': msg})
    headers = {"Content-type": "application/x-www-form-urlencoded",
                                            "Accept": "text/plain"}
    conn = http.client.HTTPConnection(endereco[0], endereco[1])
    conn.request("POST", "", params, headers)

    while True:

        
        response = conn.getresponse()
        print(response.status, response.reason)

        data = response.read()
        print (data.decode())

        msg = input("\n>>>")
        if msg == "KILL":
            msg = "KILL "
        if not msg:
            msg = "KILL"
            
        params = json.dumps({'msg': msg})
        headers = {"Content-type": "application/x-www-form-urlencoded",
                                               "Accept": "text/plain"}
        conn = http.client.HTTPConnection(endereco[0], endereco[1])
        conn.request("POST", "", params, headers)

        if msg == "KILL":
            break
    
    



def LimparTela():
    print("\n"*40)

def Valido(texto):
    invalido = ["<", ">", "/", "?", ":", "*", "|", '"']
    if texto:
        for c in texto:
            if c in invalido:
                return False
        return True

#Criptografia simples com chave simétrica
def Criptografar(texto):
    cript = []
    key = "IF975 - Projeto de Redes"
    for i in range(len(texto)):
        key_c = key[i % len(key)]
        cript_c = chr((ord(texto[i]) + ord(key_c)) % 256)
        cript.append(cript_c)
    return base64.urlsafe_b64encode("".join(cript).encode()).decode()

def Desconectar():
    tcp.send("DESCONECTAR".encode())
    tcp.close
    exit()






##################################################################



with open("ip.txt", 'r') as arquivo:
    ip = arquivo.readline()

porta = 9750

user = ""
welcome = ""
tcp = ""

Iniciar()





