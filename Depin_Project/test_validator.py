import json
import hashlib
import socket
import struct


HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)


class Userinfo:
    def __init__(self, device: str, token_choice: bool, student_id: int, trash_count: str, public_key: str):
        self.device = device
        self.token_choice = token_choice
        self.student_id = student_id
        self.trash_count = trash_count
        self.public_key = public_key


# Devices that are allowed to mint / submit sensor data
KNOWN_DEVICES = {"raspberry_pi_hub", "esp32_node"}


with open("users.json") as f:
    users = json.load(f)

accounts_by_address = {
    data["address"]: {
        "name": name,
        "balance": data["balance"],
        "student_id": data["student_id"],
        "public_key": data["public_key"],
    }
    for name, data in users.items()
}

print("User accounts:")
for name, data in users.items():
    print(f"  {name}: {data['address']} (balance={data['balance']})")
print()



def build_sample_request(user_data):
    req = {
        "device": "raspberry_pi_hub",
        "token_choice": True,
        "student_id": user_data["student_id"],
        "trash_count": "42",
        "public_key": user_data["public_key"],

        "sender": user_data["address"],
        "amount": 100,
        "balance": user_data["balance"],
    }
    req["sig"] = hashlib.sha256(
        f"{req['sender']}{req['device']}{req['student_id']}"
        f"{req['trash_count']}{req['amount']}{req['balance']}"
        f"{req['public_key']}".encode()
    ).hexdigest()
    return req


sample_requests = {name: build_sample_request(data) for name, data in users.items()}


def echo_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                req = recv_json(conn)
                print(f"Received: {req}")
                votes = [validator_1(req), validator_2(req), validator_3(req)]
                approved = votes.count(True) >= 2
                response = {
                    "approved": approved,
                    "votes": votes,
                    "message": "VALIDATORS HAVE APPROVED" if approved else "REJECTED",
                }
                print(f"Votes: {votes} -> {response['message']}")
                send_json(conn, response)


def recv_json(sock: socket.socket) -> dict:
    """Receive a length-prefixed JSON message from the socket."""
    raw_len = recvn(sock, 4)
    if not raw_len:
        raise ConnectionError("Connection closed while reading header")

    msg_len = struct.unpack(">I", raw_len)[0]

    raw_payload = recvn(sock, msg_len)
    if not raw_payload:
        raise ConnectionError("Connection closed while reading payload")

    return json.loads(raw_payload.decode("utf-8"))


def send_json(sock: socket.socket, obj: dict) -> None:
    """Send a length-prefixed JSON message."""
    payload = json.dumps(obj).encode("utf-8")
    sock.sendall(struct.pack(">I", len(payload)) + payload)


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
    body = (
        f"{req['sender']}{req['device']}{req['student_id']}"
        f"{req['trash_count']}{req['amount']}{req['balance']}"
        f"{req['public_key']}"
    ).encode()
    expected = hashlib.sha256(body).hexdigest()
    return expected == req.get("sig")


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


def has_valid_device(req):
    return req.get("device") in KNOWN_DEVICES


def has_valid_student_id(req):
    account = accounts_by_address.get(req["sender"])
    if account is None:
        return False
    return req.get("student_id") == account["student_id"]


def has_valid_trash_count(req):
    try:
        count = int(req.get("trash_count"))
    except (TypeError, ValueError):
        return False
    return 0 <= count <= 10000


def has_valid_public_key(req):
    account = accounts_by_address.get(req["sender"])
    if account is None:
        return False
    return req.get("public_key") == account["public_key"]


def validator_1(request):
    return (is_sender_known(request)
            and has_matching_balance(request)
            and has_sufficient_amount(request)
            and has_valid_device(request)
            and has_valid_student_id(request)
            and has_valid_trash_count(request)
            and has_valid_public_key(request)
            and check_signature(request))


def validator_2(request):
    return (is_sender_known(request)
            and has_matching_balance(request)
            and has_sufficient_amount(request)
            and has_valid_device(request)
            and has_valid_student_id(request)
            and has_valid_trash_count(request)
            and has_valid_public_key(request)
            and check_signature(request))


def validator_3(request):
    return (is_sender_known(request)
            and has_matching_balance(request)
            and has_sufficient_amount(request)
            and has_valid_device(request)
            and has_valid_student_id(request)
            and has_valid_trash_count(request)
            and has_valid_public_key(request)
            and check_signature(request))


print("Self-test:")
for name, req in sample_requests.items():
    votes = [validator_1(req), validator_2(req), validator_3(req)]
    result = "APPROVED" if votes.count(True) >= 2 else "REJECTED"
    print(f"  {name}: votes={votes} -> {result}")
print()

echo_server()
