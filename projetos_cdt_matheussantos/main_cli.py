import sqlite3

BANCO = "loja_camisas.db"

def listar_produtos(cursor):
    """Exibe todos os produtos cadastrados no banco de dados."""
    cursor.execute("SELECT id, nome, preco FROM produtos")
    produtos = cursor.fetchall()
    
    print("\n" + "="*40)
    print("      PRODUTOS DISPONÍVEIS NA LOJA      ")
    print("="*40)
    if not produtos:
        print("Nenhum produto cadastrado.")
    else:
        for p in produtos:
            print(f"ID: {p[0]} | {p[1]} - R$ {p[2]:.2f}")
    print("="*40)

def listar_pedidos(cursor):
    """Exibe o histórico de pedidos registrados."""
    cursor.execute("SELECT id, cliente, total, status, pagamento FROM pedidos")
    pedidos = cursor.fetchall()
    
    print("\n" + "="*40)
    print("          HISTÓRICO DE PEDIDOS          ")
    print("="*40)
    if not pedidos:
        print("Nenhum pedido registrado ainda.")
    else:
        for ped in pedidos:
            print(f"Pedido #{ped[0]} | Cliente: {ped[1]} | Total: R$ {ped[2]:.2f} | Status: {ped[3]}")
    print("="*40)

def menu():
    """Menu principal da versão em linha de comando (CLI)."""
    try:
        conn = sqlite3.connect(BANCO)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return

    while True:
        print("\n=== NAÇÃO DOS MANTOS - MODO TERMINAL (CLI) ===")
        print("1. Listar Produtos")
        print("2. Ver Histórico de Pedidos")
        print("3. Sair")
        
        opcao = input("\nEscolha uma opção (1-3): ").strip()
        
        if opcao == "1":
            listar_produtos(cursor)
        elif opcao == "2":
            listar_pedidos(cursor)
        elif opcao == "3":
            print("\nSaindo da aplicação CLI. Até logo!")
            break
        else:
            print("\nOpção inválida! Tente novamente.")

    conn.close()

if __name__ == "__main__":
    menu()