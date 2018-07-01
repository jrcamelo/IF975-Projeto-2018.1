import os, os.path
import sys
from datetime import datetime
from stat import *
import json

from Server import Gerenciador


base = os.getcwd() + "/Server/Arquivos/"


#Base para as pastas
def TemplateFolder(raiz, nome, compart):
    return {"nome": nome, "raiz": raiz, "compart": compart, "arqs": {}, "psts": {}}


#Cria o database e a pasta
def CreateProfile(user):
    if not Gerenciador.CheckExistsFolder(base):
        os.mkdir(base)
    if not Gerenciador.CheckExistsJSON(base + user + ".json"):
        CreateJSON(user)
    if not Gerenciador.CheckExistsFolder(base + user + "/"):
        os.mkdir(base + user)        


#Todo o Database é feito por JSON
#É um dicionário com todas as pastas
#Onde as pastas são dicionários
#Que tem suas informações, e outros 2 dicionários dentro dela
#São os dicionários de Pastas filhas e Arquivos
def CreateJSON(user):
    template = {'':TemplateFolder("NONE", "", "")}  
    with open(base + user + ".json", "w") as file:
        json.dump(template, file, indent=8)

def LoadJSON(user):
    if not Gerenciador.CheckExistsJSON(base + user + ".json"):
        return ""
    with open(base + user + ".json") as file:
        return json.load(file)


def WriteJSON(user, dados):
    with open(base + user + ".json", "w") as file:
        json.dump(dados, file, indent=8)


#Constrói um texto com todas pastas e arquivos presentes em uma pasta
#Esse texto é enviado para e interpretado pelo Cliente
#Que o usa para ajudar na navegação
def ContentFolder(index, user, caminho):
    if caminho.endswith(".."):
        caminho = '/'.join(caminho[:-3].split("/")[:-1])
    if caminho == "/": caminho = ""
    
    if not caminho in index:
        return {}, "<Pasta não encontrada!>"

    pasta = index[caminho]
    vazia = True
    result = caminho + "\n"
    shared = ""
    if pasta['compart'] != []:
        shared = ", ".join(pasta['compart'])
    if shared:
        result += "Compartilhada com: " + shared + "\n"
    for filho in list(pasta['psts'].keys()):
        result += "\n>>" + filho
        vazia = False
    for file in list(pasta['arqs'].keys()):
        result += "\n  " + file
        vazia = False
        
    if vazia:
        result +="\n<PASTA VAZIA>"

    return result, ""

#Adiciona um novo dicionário no database
#Pode sobrescrever pastas anteriores
#Simplesmente deletando-a e criando uma nova por cima
#Pode manter as informações e compartilhamentos
def AddFolder(index, user, caminho, pasta, conteudo = "", sobrescrever=False, mover=False, compart=[]):
    if not caminho in index:
        return {}, "<Caminho inválido!>"
    if Path(caminho, pasta) in index and not sobrescrever:
        return {}, "<Pasta já existe!>"

    err = ""
    if not mover:
        err = Gerenciador.CreateFolder(user, Path(caminho, pasta))
        if err: return {}, err
    if not conteudo: conteudo = TemplateFolder(caminho, pasta, compart)
    index[Path(caminho, pasta)] = conteudo
    index[caminho]['psts'][pasta] = Path(caminho, pasta)        
    return index, err


def CheckUpload(index, user, caminho, nome):
    if not caminho in index:
        return "<Caminho inválido!>"
    if nome in index[caminho]['arqs']:
        return "<Arquivo já existe!>"
    return ""

def CheckFile(index, user, caminho, nome):
    if not caminho in index:
        return "<Caminho não existe!>"
    if not nome in index[caminho]['arqs']:
        return "<Arquivo não existe!>"
    return

def CheckFolder(index, user, caminho, nome, up=False):
    if not caminho in index:
        return "<Caminho não existe!>"
    if not nome in index[caminho]['psts'] and not up:
        return "<Pasta não existe!>"    
    if nome in index[caminho]['psts'] and up:
        return "<Pasta já existe!>"
    return

def CheckShareFile(index, user, caminho, nome):
    if not caminho in index:
        return "<Caminho não existe!>"
    if not nome in index[caminho]['arqs']:
        return "<Arquivo não existe!>"    
    return index[caminho]['arqs'][nome]

def CheckShareFolder(index, user, caminho):
    if not caminho in index:
        return "<Pasta não existe!>"
    return index[caminho]['compart']


#Adiciona um item no dicionário de arquivos da pasta
def AddFile(index, user, caminho, nome, sobrescrever=False, compart=[]):
    if not caminho in index:
        return {}, "<Caminho inválido!>"
    if not sobrescrever and nome in index[caminho]['arqs']:
        return {}, "<Arquivo já existe!>"

    index[caminho]['arqs'][nome] = compart
    return index, ""

#Devolve o caminho verdadeiro de um arquivo, caso ele exista
def GetFile(index, user, caminho, nome):
    if not caminho in index:
        return "", "<Caminho inválido!>"
    if not nome in index[caminho]['arqs']:
        return "", "<Arquivo não encontrado!>"
    return Gerenciador.PathServer(user, Path(caminho, nome)), ""

def RemoveFile(index, user, caminho, nome):
    if not caminho in index:
        return {}, "<Caminho inválido!>"
    if not nome in index[caminho]['arqs']:
        return {}, "<Arquivo não existe!>"
    
    index[caminho]['arqs'].pop(nome)
    return index, ""

#Adiciona um arquivo novo com as informações do que está sendo movido
#Então logo em seguida deleta o arquivo anterior
#Pesquisar experimento do Homem do Pântano :)
def MoveFile(index, user, caminho, nome, destino, novoNome="", sobrescrever=False):
    if not caminho in index:
        return {}, "<Caminho inválido!>"
    if not nome in index[caminho]['arqs']:
        return {}, "<Arquivo não existe!>"
    
    if not novoNome: novoNome = nome
    compart = index[caminho]['arqs'][nome]
    index, err = AddFile(index, user, destino, novoNome, sobrescrever, compart)
    if err: return {}, err
    index, err = RemoveFile(index, user, caminho, nome)
    if err: return {}, err
    return index, err


def ShareFile(index, user, caminho, nome, compart):
    if not caminho in index:
        return {}, "", "<Caminho inválido!>"
    if not nome in index[caminho]['arqs']:
        return {}, "", "<Arquivo não existe!>"
    index[caminho]['arqs'][nome] = compart
    return index, ""

def ShareFolder(index, user, caminho, compart):
    if not caminho in index:
        return {}, "", "<Pasta não encontrada!>"
    index[caminho]['compart'] = compart
    return index, ""


#Função recursiva que apaga todas entradas de pastas filhas da pasta deletada
#Também apaga as menções da pasta na raíz dela
def RemoveFolder(index, user, caminho):
    if not caminho in index:
        return {}, "<Pasta não encontrada!>"

    err = ""
    #Mata os filhos da pasta
    filhos = list(index[caminho]['psts'].keys())
    for f in filhos:
        index, err = RemoveFolder(index, user, index[caminho]['psts'][f]) 
        if err: return {}, err
        
    raiz = index[caminho]['raiz']
    nome = index[caminho]['nome']
    
    if raiz != "NONE":
        index[raiz]['psts'].pop(nome)
    index.pop(caminho) 
    return index, err


#Função recursiva que deu bastante trabalho
#Cria uma nova pasta no novo caminho ou nome
#Chama a função novamente para cada pasta filha
#Depois que as pastas são criadas
#São preenchidas com as informações corrigidas da antiga
#Então a antiga é deletada
#A pasta escolhida para ser movida é a primeira a ser criada
#Mas por sua vez é a última a ser deletada
def MoveFolder(index, user, caminho, novoCaminho, novoNome=""):
    if not caminho in index:
        return {}, "<Caminho inválido!>" 
    pasta = index[caminho]
    nome = pasta['nome']
    raiz = pasta['raiz']
    compart = pasta['compart']
    print(compart)
    if not novoNome: novoNome = nome
    pasta['nome'] = novoNome
    if raiz != novoCaminho :        
        pasta['raiz'] = novoCaminho
    if raiz != "NONE":
        index[raiz]['psts'].pop(nome)        
        
    novo = Path(novoCaminho, novoNome)
    if novo in index:
        return {}, "<Pasta já existe!>"
    if novo.startswith(caminho):
        return {}, "<Inception: Pastas não são recursivas!>"    

    index, err = AddFolder(index, user, novoCaminho, novoNome, "", True, True, compart)    
    if pasta['psts']: index[novo]['psts'] = pasta['psts']
    if pasta['arqs']: index[novo]['arqs'] = pasta['arqs']
    if err: return {}, err

    filhos = list(pasta['psts'].keys())
    for f in filhos:
        index, err = MoveFolder(index, user, index[caminho]['psts'][f], novo)

    index.pop(caminho)
    return index, err


#Desfaz e refaz caminhos para incluir algo novo
#Poderia ser mais simples, mas assim é mais seguro
def Path(caminho, destino = ""):
    path = ""
    caminho = caminho.split("/")
    if destino: caminho.append(destino)
    for c in caminho:
        if c: path += "/" + c
    return path


#Função recursiva que funcionou melhor do que o esperado
#Explora um Índice de outrem com as permissões do usuário
def ExploreShared(index, newindex, user, path):
    pasta = index[path]


    #Caso uma pasta seja compartilhada, tudo dentro dela é compartilhado
    #No caso da raíz ser assim, o usuário tem acesso a tudo dentro dela
    if user in pasta['compart']:
        newindex[path] = index[path]
        for filho in pasta['psts']:
            filho = pasta['psts'][filho]
            newindex[filho] = index[filho]
            newindex = GetAllFilhos(index, newindex, filho)
        return newindex, 1

    share = 0
        
    newpasta = {}
    newpasta['arqs'] = {}
    newpasta['psts'] = {}

    #Mas nem sempre esse é o caso
    #Se somente um arquivo for compartilhado dentro de uma pasta
    #O usuário tem acesso a todas pastas no caminho dela
    #Mas não podem ver pastas ou arquivos não compartilhados
    for arq in pasta['arqs']:
        if user in pasta['arqs'][arq]:
            if share == 0:
                share = 1
                newindex[path] = {}
            newpasta['arqs'][arq] = pasta['arqs'][arq]

    #O mesmo acontece com as pastas
    #Onde tudo dentro dela é compartilhado
    #Mas o seu caminho precisa ser acessivel
    #Então o usuário tem acesso parcial às que estão no caminho
    #Podendo somente ver o seu nome
    for pst in pasta['psts']:
        filho = pasta['psts'][pst]
        newindex, isShare = ExploreShared(index, newindex, user, filho)
        if isShare > 0:
            if share == 0:
                share = 1
                newindex[path] = {}
            newpasta['psts'][pst] = filho

    #As pastas de acesso parcial não mostram com quem elas são compartilhadas
    #Por questão de segurança e privacidade
    #No índice que é passado para o Usuário, só há informações que ele tem acesso
    #Sendo completamente separado do Índice original
    if share:
        newindex[path]['nome'] = pasta['nome']
        newindex[path]['raiz'] = pasta['raiz']
        newindex[path]['compart'] = []        
        newindex[path]['arqs'] = newpasta['arqs']
        newindex[path]['psts'] = newpasta['psts']
    
    return newindex, share


#Método auxiliar para a ExploreShared      
def GetAllFilhos(index, newindex, path):
    pasta = index[path]
    for neto in pasta['psts']:
        neto = pasta['psts'][neto]
        newindex[neto] = index[neto]
        newindex = GetAllFilhos(index, newindex, neto)
    return newindex







            






