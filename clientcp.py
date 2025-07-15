import socket

target_host = "127.0.0.1"
target_port = 9998

#AF_INET -> vai usar ipv4, SOCK_STREAM mostra que será TCP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#vai conectar nos endereços que passamos
client.connect((target_host,target_port))

#mandando pacote para o server tcp que foi criado
client.send(b"Testando... 1 2 3")

#reposta
response = client.recv(4096)

print(response.decode())
client.close()