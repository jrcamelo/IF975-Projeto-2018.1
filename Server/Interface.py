from Server import Indexador
from Conexoes import Comunicador
from random import randint


#Essa é a classe com mais usos
#É bem robusta e foi bem testada
#Trata todas as mensagens do cliente
#Porém é mais Programação que Redes
#Logo não vai ser tão explicada
class Usuario():

    def __init__(self, Serv, conn):
        self.Serv = Serv
        self.conn = conn
        self.user = ""
        self.name = ""
        self.index = ""
        self.sharedIndex = ""
        self.sharedUser = ""
        
       
    def SalvarIndex(self, index):
        if index == "":
            return "<Erro na indexação>"
        err = Indexador.WriteJSON(self.user, index)
        if not err:
            self.index = index
        return err
    

    #Método que é chamado pelo servidor
    def Executar(self, comandos):
        
        if not "::" in comandos:
            #Seria o resto de alguma mensagem anterior
            return

        #Todos os comandos enviados pelo cliente tem :: como separador
        #Usar espaços pode trazer problemas ao tratar de nomes e caminhos
        comandos = comandos.split("::")

        #Esses métodos não modificam o índice
        metodos = {
                    "REGISTER": self.Registrar,
                    "LOGIN": self.Logar,
                    "TEST": self.TestarConexao,
                    "LS": self.ListarPasta,
                    "GET": self.DownloadArquivo,
                    "LOAD": self.LoadShared,
                    "OTHERS": self.ListarOnline,
                    "CHECK": self.ChecarArquivo,
                    "CHECKDIR": self.ChecarPasta,
                    "CHECKSHARE": self.ChecarCompart,
                    "LITTLEZERO": self.ListarLobby,
                    "ORONE": self.EntrarLobby
            }
        metodo = metodos.get(comandos[0], "")
        if metodo:
            return metodo(comandos[1:]) 


        #Esses métodos modificam o índice
        metodos = {
                    "MKDIR": self.CriarPasta,
                    "POST": self.UploadArquivo,
                    "DELETE": self.DeletarArquivo,
                    "DELDIR": self.DeletarPasta,
                    "MOVE": self.MoverArquivo,  
                    "MOVEDIR": self.MoverPasta,
                    "SHARE": self.Compartilhar,
                    "SHAREDIR": self.CompartilharPasta                
            }
        metodo = metodos.get(comandos[0], self.Invalido)

        #Recebe o Índice modificado e possíveis erros
        novoIndex, err = metodo(comandos[1:])
        
        #Caso haja algum erro, o Índice não é salvo
        if not err:
            err = self.SalvarIndex(novoIndex)
        #Os erros são devolvidos para o servidor
        #Caso realmente tenha acontecido um erro, ele é enviado para o cliente
        return err
    

    def Invalido(self, comandos):
        return "", "<Comando Inválido!>"
    

    #Tudo feito na parte do Servidor mesmo
    def Registrar(self, comandos):
        u = comandos[0][1:][:-1].lower()
        self.Serv.CreateUser(self.conn, u)
        

    #Maior parte feita pelo Servidor
    #Mas preenche os dados na classe do Usuário
    def Logar(self, comandos):
        #Remove os < >
        u = comandos[0][1:][:-1].lower()
        name, err = self.Serv.Login(self.conn, u)

        if name:            
            self.user = u
            self.name = name

            #Cria os arquivos do banco de dados
            Indexador.CreateProfile(self.user)           
            self.index = Indexador.LoadJSON(self.user)
        return err


    #1 questão
    #Mais explicações estarão no arquivo Conexoes.py
    def TestarConexao(self, comandos):
        tipo = comandos[0]
        rand = randint(1, 1000)

        com = Comunicador(self.Serv.ip, rand, tipo)
        porta = com.EscolherPorta()
        if not porta:
            return "<ERRO>"
        
        self.Serv.SendMessage(self.conn, porta, "")
        com.Comunicar()
        return ""
        
        
    
    
    #Não modifica index, envia mensagem
    #Devolve um texto sobre os conteúdos das pastas
    #Ver mais no Indexador.py
    #Caso tente acessar um arquivo, o Cliente é avisado
    #O que permite que ele baixe arquivos diretamente pelo LS
    def ListarPasta(self, comandos):
        caminho = comandos[0][1:][:-1]

        index = self.index
        user = self.user
        if len(comandos) > 1:
            if comandos[1] == "SHARED":
                index = self.sharedIndex
                user = self.sharedUser
            
        conteudo, err = Indexador.ContentFolder(index, user, caminho)
        if err:
            if Indexador.Gerenciador.PathFile(user, caminho):
                return "[CAMINHO SELECIONADO É UM ARQUIVO]"
            return err
        return conteudo

    
    #Não modifica index, envia mensagem
    def DownloadArquivo(self, comandos):
        minComandos = 2
        if not comandos:
            return "", "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "", "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        nome = comandos[1]
        index = self.index
        user = self.user
        if len(comandos) > minComandos:
            if comandos[2] == "SHARED":
                index = self.sharedIndex
                user = self.sharedUser
            

        #Indexador checa se arquivo existe
        #E devolve o caminho verdadeiro do arquivo
        arquivo, err = Indexador.GetFile(index, user, caminho, nome)
        if err:
            return err

        #Informa o tamanho do arquivo
        tamanho = Indexador.Gerenciador.Size(arquivo)
        #E o servidor envia
        err = self.Serv.SendFile(self.conn, self.user, arquivo, tamanho)        
        return err
    

    #Não modifica index, envia mensagem
    #Carrega o índice de outro usuário
    #Considera as permissões de acesso do usuário que tenta acessar
    #E constrói um índice somente daquilo que ele pode acessar
    #Ver mais no Indexador.py
    def LoadShared(self, comandos):
        outro = comandos[0]
        
        outroIndex = Indexador.LoadJSON(outro)
        if not outroIndex:
            return "<USUÁRIO NÃO ENCONTRADO!>"
        
        sharedIndex, isShare = Indexador.ExploreShared(outroIndex, {}, self.user, "")
        if not isShare:
            return "<SEM PERMISSÃO PARA ACESSAR!>"
        
        self.sharedIndex = sharedIndex
        self.sharedUser = outro
        return "OK"
    

    #Não modifica index, envia mensagem
    #Devolve uma lista dos usuários online
    def ListarOnline(self, comando):
        if comando[0] == "LIST":        
            lista = self.Serv.ShowUsers(self.user)
            conteudo = "\n".join(lista)
            if not conteudo:
                return "[NENHUM USUÁRIO ONLINE]"
            return conteudo


    #Não modifica index, envia mensagem, devolve só err
    #Checa a existência de algum arquivo, o seu tamanho e caminho
    #Serve mais para validação de Download e Upload
    def ChecarArquivo(self, comandos):
        minComandos = 2
        if not comandos:
            return "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        nome = comandos[1]
        up = False
        if len(comandos) > minComandos:
            up = True

        if up:
            err = Indexador.CheckUpload(self.index, self.user, caminho, nome)
            if not err:
                self.Serv.SendMessage(self.conn, "OK", "")
            return err
            
        err = Indexador.CheckFile(self.index, self.user, caminho, nome)
        if err:
            return err

        path = Indexador.Path(caminho, nome)
        tamanho = Indexador.Gerenciador.SizeUser(self.user, path)
        
        self.Serv.SendMessage(self.conn, str(tamanho), "")
    

    #Não modifica index, envia mensagem, devolve só err
    #Mesma coisa do ChecarArquivo, mas com Pasta
    def ChecarPasta(self, comandos):
        minComandos = 2
        if not comandos:
            return "", "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "", "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        nome = comandos[1]
        up = False
        if len(comandos) > minComandos:
            up = True

        err = Indexador.CheckFolder(self.index, self.user, caminho, nome, up)
        if not err:
            self.Serv.SendMessage(self.conn, "OK", "")
        return err

    
    #Não modifica index, envia mensagem
    #Devolve uma string de quem o arquivo ou pasta está compartilhado
    def ChecarCompart(self, comandos):
        minComandos = 1
        if not comandos:
            return "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        nome = ""
        if len(comandos) > 1:
            nome = comandos[1]

        if nome:
            compart = Indexador.CheckShareFile(self.index, self.user, caminho, nome)
        else:
            compart = Indexador.CheckShareFolder(self.index, self.user, caminho)

        if not compart:
            compart = "[NINGUÉM]"
        elif type(compart) == type([]):
            compart = " | ".join(compart)

        self.Serv.SendMessage(self.conn, compart, "")


    #3 questão
    #Devolve uma lista dos usuários online no servidor do jogo
    def ListarLobby(self, comandos):
        pessoas = self.Serv.Lobby.ListarJogadores()
        self.Serv.SendMessage(self.conn, pessoas, "")

    #3 questão
    #Adiciona o jogador no servidor do jogo, junto com seu número escolhido
    def EntrarLobby(self, comandos):
        numero = int(comandos[0])
        porta = self.Serv.Lobby.AdicionarJogador(self.user, numero)
        self.Serv.SendMessage(self.conn, str(porta), "")
        
        
        
    

    
    #Modifica index, retorna-o, OK
    #Ver Indexador.py
    def CriarPasta(self, comandos):
        minComandos = 2
        if not comandos:
            return "", "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "", "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        nome = comandos[1]
        subst = False
        if len(comandos) > minComandos:
            subst = comandos[2]
            
        novoIndex, err = Indexador.AddFolder(self.index, self.user, caminho, nome)
        if not err:
            self.Serv.SendMessage(self.conn, "OK", "")
        return novoIndex, err


    #Modifica index, retorna-o
    #Primeiro checa se o caminho do upload é válido
    #Se arquivo já existir, avisa ao cliente
    #Que pode ignorar e fazer um PUT, que substitui
    #Mais informações no Servidor.py
    def UploadArquivo(self, comandos):
        minComandos = 3
        if not comandos:
            return "", "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "", "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        nome = comandos[1]
        tamanho = int(comandos[2])
        subst = False
        if len(comandos) > minComandos:
            subst = True

        if not subst:
            err = Indexador.CheckUpload(self.index, self.user, caminho, nome)
            print(err)
            if err:
                self.Serv.SendMessage(self.conn, err, "")
                return "", err

        path = Indexador.Path(caminho, nome)
        pathServer = Indexador.Gerenciador.PathServer(self.user, path)
        err = self.Serv.GetFile(self.conn, self.user, pathServer, tamanho)
        if err:
            self.Serv.SendMessage(self.conn, err, "")
            return "", err
        
        novoIndex, err = Indexador.AddFile(self.index, self.user, caminho, nome, subst)
        if err:
            Indexador.Gerenciador.os.remove(pathServer)
        return novoIndex, err
     

    #Modifica index, retorna-o, OK
    #Tenta deletar do índice
    #Se o arquivo for valido
    #Deleta o arquivo em si
    def DeletarArquivo(self, comandos):
        minComandos = 2
        if not comandos:
            return "", "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "", "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        nome = comandos[1]        
        
        novoIndex, err = Indexador.RemoveFile(self.index, self.user, caminho, nome)

        if err:
            return "", err

        path = Indexador.Path(caminho, nome)
        path = Indexador.Gerenciador.PathServer(self.user, path)
        err = Indexador.Gerenciador.DeleteFile(path)

        if err:
            return "", err    

        self.Serv.SendMessage(self.conn, "OK", "")
        return novoIndex, err
        

    #Modifica index, retorna-o, OK
    #Tenta deletar do índice
    #Inclusive todos seus filhos e arquivos
    #Se for válido
    #Deleta a pasta e tudo que há nela
    def DeletarPasta(self, comandos):
        minComandos = 1
        if not comandos:
            return "", "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "", "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        
        if not caminho:
            return "<NÃO PODE DELETAR A RAÍZ!!!>"
        
        novoIndex, err = Indexador.RemoveFolder(self.index, self.user, caminho)
        if err:
            self.Serv.SendMessage(self.conn, err, "")
            return "", err

        path = Indexador.Gerenciador.PathServer(self.user, caminho)
        err = Indexador.Gerenciador.DeleteFolders(path)

        if err:            
            return "", err
        
        self.Serv.SendMessage(self.conn, "OK", "")
        return novoIndex, err
    

    #Modifica index, retorna-o, OK
    #Move ou renomeia um arquivo
    #Adicionando um novo e depois apagando o antigo
    def MoverArquivo(self, comandos):
        minComandos = 4
        if not comandos:
            return "", "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "", "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        nome = comandos[1]
        destino = comandos[2][1:][:-1]
        novoNome = novoNome = comandos[3]
            
        novoIndex, err = Indexador.MoveFile(self.index, self.user, caminho, \
                                            nome, destino, novoNome, True)
        if err:
            return "", err

        pathOld = Indexador.Path(caminho, nome)
        pathNew = Indexador.Path(destino, novoNome)
        err = Indexador.Gerenciador.Move(self.user, pathOld, pathNew)

        if err:            
            return "", err
        
        self.Serv.SendMessage(self.conn, "OK", "")        
        return novoIndex, err

    
    #Modifica index, retorna-o, OK
    #Complicado de implementar, mas deu tudo certo
    #Move ou renomeia todos arquivos e pastas
    #Inclusive reestruturando as informações
    #Mantém compartilhamentos e arquivos sem problema
    def MoverPasta(self, comandos):
        minComandos = 4
        if not comandos:
            return "", "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "", "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        nome = comandos[1]
        novoCaminho = comandos[2][1:][:-1]
        novoNome = comandos[3]

        caminho = Indexador.Path(caminho, nome)
        novoIndex, err = Indexador.MoveFolder(self.index, self.user, caminho, \
                                              novoCaminho, novoNome)
        if err:
            return "", err

        caminhoNovo = Indexador.Path(novoCaminho, novoNome)
        err = Indexador.Gerenciador.MoveFolder(self.user, caminho, caminhoNovo)

        if err:
            return "", err        
        
        self.Serv.SendMessage(self.conn, "OK", "")
        return novoIndex, err  


    #Modifica Index, retorna-o, OK
    #Muda a informação de compartilhamento de um arquivo
    def Compartilhar(self, comandos):
        minComandos = 3
        if not comandos:
            return "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        nome = comandos[1]
        compart = comandos[2][1:][:-1]
        
        compart = compart.split(" | ")
        novoIndex, err = Indexador.ShareFile(self.index, self.user, caminho, nome, compart)
        if not err:
            self.Serv.SendMessage(self.conn, "OK", "")
        return novoIndex, err
    
    #Modifica Index, retorna-o, OK
    #Muda a informação de compartilhamento de uma pasta
    #Se uma pasta for compartilhada, tudo que há nela
    #Inclusive filhos das pastas filhos, serão compartilhados também
    #Mas somente a pasta compartilhada tem a informação de compartilhamento
    def CompartilharPasta(self, comandos):
        minComandos = 2
        if not comandos:
            return "<Sem comandos!>"
        elif len(comandos) < minComandos:
            return "<Comando inválido!>"
        caminho = comandos[0][1:][:-1]
        compart = comandos[1][1:][:-1]
        
        compart = compart.split(" | ")
        novoIndex, err = Indexador.ShareFolder(self.index, self.user, caminho, compart)
        if not err:
            self.Serv.SendMessage(self.conn, "OK", "")
        return novoIndex, err
                
    

                
                
        

        
        
        
