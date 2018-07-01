import os, os.path
import sys
from datetime import datetime
from stat import *
import shutil

base = os.getcwd() + "/Server/Arquivos/"

#Gerenciador.py é a parte que altera os arquivos de verdade



def CreateFolder(user, caminho):
    caminho = PathServer(user, caminho)
    os.mkdir(caminho)
    return ""

def DeleteFile(caminho):
    try:
        os.remove(caminho)
        return ""
    except:
        return "<ERRO AO DELETAR ARQUIVO>"

#Shutil deleta tudo que há na pasta
def DeleteFolders(caminho):
    try:
        shutil.rmtree(caminho, ignore_errors=True)
        return ""
    except:
        return "<ERRO AO DELETAR PASTAS>"

#Shutil move tudo que há na pasta
def Move(user, old, new):
    old = PathServer(user, old)
    new = PathServer(user, new)

    try:
        shutil.move(old, new)
    except:
        return "<ERRO AO MOVER ARQUIVO>"
    return ""

#Shutil copia tudo que há na pasta
def MoveFolder(user, old, new):
    old = PathServer(user, old)
    new = PathServer(user, new)

    try:
        shutil.copytree(old, new)        
        DeleteFolders(old)
    except:
        return "<ERRO AO MOVER PASTAS>"    
    return ""
    

def SizeUser(user, caminho):
    caminho = PathServer(user, caminho)
    return Size(caminho)

def Size(caminho):
    try:
        size = os.path.getsize(caminho)
    except:
        return "<ERRO NO TRATAMENTO DE ARQUIVOS>"
    return size


#Devolve caminho verdadeiro
def PathServer(user, path):
    while path.endswith("/"):
        path = path[:-1]
    return base + user + "/" + path


def PathExists(user, path):
    return os.path.exists(PathServer(user, path))
def PathFile(user, path):
    return os.path.isfile(PathServer(user, path))
def PathFolder(user, path):
    return os.path.isdir(PathServer(user, path))

#Não usa PathServer
def PathBack(path):
    while path.endswith("/"):
        path = path[:-1]
    return '/'.join(path.split("/")[:-1])

def CheckExistsJSON(path):
    return os.path.isfile(path)
def CheckExistsFolder(path):
    return os.path.isdir(path)





