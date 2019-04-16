#Webapp para gerenciamento de restaurantes e seus respectivos menus

Esse código em Python oferece um Webapp que permite o gerenciamento,por meio de login de acesso, 
de restaurantes e seus respectivos menus a fim de cadastrar,excluir, editar 
e consultar seus produtos persistidos em banco de dados relacional.

##Versão

A versão utilizada foi 2.7.16 do Python

##Procedimetos

* Primeiramente para executar o código, será necessário instalar uma máquina virtual com o `VirtualBox` disponivel no link https://www.virtualbox.org/wiki/Downloads
* Caso seu sistema operacional seja Mac ou Linux, faz necessário baixar o Git Bach como terminal shell. https://git-scm.com/downloads
* Após a instalação você deverá baixar e instalar o `Vagrant` que é uma ferramenta que permite o compartilhamento e gerenciamento de arquivo via VM.
* Para teste utilize o terminal e execute **vagrant --version** para verificar se está tudo funcionando
* Faça um clone desse diretório pronto para compartilhamento https://github.com/udacity/fullstack-nanodegree-vm/
* Pela execução do git percorra até o diretório de compartilhamento (ex: `C:/Downloads/FSND-Virtual-Machine`) e execute o comando **vagrant up**
* Ele irá baixar todos os arquivos necessários e instalar para realização de compartilhamento entre máquinas virtuais.
* Quando terminar a execução logue na VM pelo comando **vagrant ssh**
* Instale todas as dependendências necessárias atráves do **pip** executando o arquivo `requirements.txt`
* No seu terminal, já conectado com o vagrant e no diretório do projeto, execute o comando `pip install -r requirements.txt` para instalação das dependências
* Para criação de estruturas de banco como tabelas e seus mapeamentos pelo `sqlalchemy` atráves da execução do arquivo **database_setup.py**.
* A carga de dados deve ser executado o arquivo **lotesofmenus.py**
* Isso deverá ser feito atráves de VM pelo vagrant, já previamente instalado e configurado.
* Ao executar as querys as tabelas **user**, **restaurant** e **menu_item** serão criados e populados.
* Com os dados populados, basta executar o arquivo **restaurantapp.py**

##Conteúdo

* `database_setup.py`(Código fonte que realiza o mapemanto das entidades de banco de dados).
* `lotesofmenus.py`(Código fonte que realiza a carga inicial dos dados).
* `restaurantapp.py`(Código fonte que inicializa a aplicação web junto com servidor em máquina local).