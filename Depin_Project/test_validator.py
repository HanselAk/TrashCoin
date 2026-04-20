import json
import hashlib
import socket
import struct

HOST = "40.20.4.5"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)


with open("users.json") as f:
    users = json.load(f)

accounts_by_address = {
    data["address"]: {"name": name, "balance": data["balance"]}
    for name, data in users.items()
}

print("User accounts:")
for name, data in users.items():
    print(f"  {name}: {data['address']} (balance={data['balance']})")
print()

request = {
    "Device" : str ,
    "Tokenchoice" :bool ,
    "StudentID" : int ,
    "Trashcount"  : str,
    "PublicKey" : str,


    
    "sender": users["Hansel"]["address"],
    "amount": 100,
    "balance": users["Hansel"]["balance"]
}



def echo_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                data = recv_json(conn)
                print(data)
                if not data:
                    break
                print(f"Received data: {data.decode()}")
                conn.sendall(data)  # Echo back the received data







def recv_json(sock: socket.socket) -> dict:
    """Receive a length-prefixed JSON message from the socket."""
    # Read exactly 4 bytes for the length header
    raw_len = recvn(sock, 4)
    if not raw_len:
        raise ConnectionError("Connection closed while reading header")

    msg_len = struct.unpack(">I", raw_len)[0]

    # Read exactly msg_len bytes for the payload
    raw_payload = recvn(sock, msg_len)
    if not raw_payload:
        raise ConnectionError("Connection closed while reading payload")

    data= json.loads(raw_payload.decode("utf-8"))

    return data["device"]



    





def recvn(sock: socket.socket, n: int) -> bytes:
    """Read exactly n bytes from the socket."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return b"" 
        buf += chunk
    return buf
   

def recvn(sock: socket.socket, n: int) -> bytes:
    """Read exactly n bytes from the socket."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return b""
        buf += chunk
    return buf












def check_signature(req):
    body = f"{req['sender']}{req['message']}{req['amount']}{req['balance']}".encode()
    expected = hashlib.sha256(body).hexdigest()
    return expected == req.get("sig")

# Example signature generation for this demo request
# request["sig"] = hashlib.sha256(
#  #   f"{request['sender']}{request['message']}{request['amount']}{request['balance']}".encode()
# ).hexdigest()


def is_sender_known(req):
    return req["sender"] in accounts_by_address


def has_matching_balance(req):
    account = accounts_by_address.get(req["sender"])
    if account is None:
        return False
    return req.get("balance") == account["balance"]


def has_sufficient_amount(req):
    account = accounts_by_address.get(req["sender"])
    if account is None:
        return False
    return req["amount"] <= account["balance"]





def validator_1(request):
    return is_sender_known(request) and has_matching_balance(request) and has_sufficient_amount(request) and check_signature(request)


def validator_2(request):
    return is_sender_known(request) and has_matching_balance(request) and has_sufficient_amount(request) and check_signature(request)


def validator_3(request):
    return is_sender_known(request) and has_matching_balance(request) and has_sufficient_amount(request) and check_signature(request)

echo_server()


votes = [validator_1(request), validator_2(request), validator_3(request)]
print("Votes:", votes)

if votes.count(True) >= 2:
    print("VALIDATORS HAVE APPROVED")
else:
    print("REJECTED")
