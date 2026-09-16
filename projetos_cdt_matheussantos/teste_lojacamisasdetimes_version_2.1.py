import json
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from faker import Faker

# ==========================================
# CONFIGURAÇÕES
# ==========================================

NOME_LOJA = "BRASIL CAMISAS"
ARQUIVO_JSON = "configuracao.json"
BANCO_DADOS = "loja_camisas.db"
PRECO_PERSONALIZACAO = 20.00  # Taxa fixa para nome + número

fake = Faker("pt_BR")

times = [
    "Athletico-PR",
    "Atletico-MG",
    "Bahia",
    "Botafogo",
    "Chapecoense",
    "Corinthians",
    "Coritiba",
    "Cruzeiro",
    "Flamengo",
    "Fluminense",
    "Gremio",
    "Internacional",
    "Mirassol",
    "Palmeiras",
    "Red Bull Bragantino",
    "Remo",
    "Santos",
    "Sao Paulo",
    "Vasco",
    "Vitoria",
]

precos = {time: 120.00 + (i * 5) for i, time in enumerate(times)}

# ==========================================
# BANCO DE DADOS SQLITE
# ==========================================

conexao = sqlite3.connect(BANCO_DADOS)
cursor = conexao.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    detalhes TEXT NOT NULL,
    total REAL NOT NULL,
    data TEXT NOT NULL
)
""")

conexao.commit()

# Popula os produtos no banco
cursor.execute("SELECT COUNT(*) FROM produtos")
if cursor.fetchone()[0] == 0:
    for time in times:
        cursor.execute(
            "INSERT INTO produtos (nome, preco) VALUES (?, ?)",
            ("Camisa " + time, precos[time]),
        )
    conexao.commit()

# Configuração JSON
configuracao = {
    "nome_loja": NOME_LOJA,
    "categoria": "Camisas de Times Brasileiros",
    "quantidade_times": len(times),
    "times": times,
}

with open(ARQUIVO_JSON, "w", encoding="utf-8") as arquivo:
    json.dump(configuracao, arquivo, ensure_ascii=False, indent=4)

# ==========================================
# JANELA PRINCIPAL
# ==========================================

janela = tk.Tk()
janela.title(NOME_LOJA)
janela.geometry("1150x750")
janela.minsize(1000, 650)

carrinho = []

# ==========================================
# FUNÇÕES DE NEGÓCIO
# ==========================================


def atualizar_total():
    total = sum(item["subtotal"] for item in carrinho)
    label_total.config(text=f"Total: R$ {total:.2f}")


def atualizar_carrinho():
    lista_carrinho.delete(*lista_carrinho.get_children())
    for item in carrinho:
        pers_str = "Sim" if item["personalizado"] else "Não"
        lista_carrinho.insert(
            "",
            "end",
            values=(
                item["produto"],
                item["tamanho"],
                pers_str,
                item["quantidade"],
                f"R$ {item['subtotal']:.2f}",
            ),
        )
    atualizar_total()


def alternar_campos_personalizacao():
    if var_personalizar.get():
        campo_nome_camisa.config(state="normal")
        campo_numero_camisa.config(state="normal")
    else:
        campo_nome_camisa.delete(0, tk.END)
        campo_numero_camisa.delete(0, tk.END)
        campo_nome_camisa.config(state="disabled")
        campo_numero_camisa.config(state="disabled")


def adicionar_carrinho():
    selecionado = tabela.selection()

    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione uma camisa da lista.")
        return

    item = tabela.item(selecionado[0])
    valores = item["values"]

    produto = valores[1]
    preco_base = float(valores[2])
    tamanho = combo_tamanho.get()

    try:
        quantidade = int(campo_quantidade.get().strip())
        if quantidade <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Erro", "Digite uma quantidade válida (número inteiro positivo)."
        )
        return

    is_personalizado = var_personalizar.get()
    nome_pers = campo_nome_camisa.get().strip() if is_personalizado else ""
    num_pers = campo_numero_camisa.get().strip() if is_personalizado else ""

    if is_personalizado and (not nome_pers or not num_pers):
        messagebox.showwarning(
            "Aviso", "Preencha o Nome e o Número para personalizar a camisa."
        )
        return

    preco_unitario = preco_base + (
        PRECO_PERSONALIZACAO if is_personalizado else 0.0
    )
    subtotal = preco_unitario * quantidade

    # Se tiver personalização individual, não agrupa
    item_existente = None
    if not is_personalizado:
        item_existente = next(
            (
                i
                for i in carrinho
                if i["produto"] == produto
                and i["tamanho"] == tamanho
                and not i["personalizado"]
            ),
            None,
        )

    if item_existente:
        item_existente["quantidade"] += quantidade
        item_existente["subtotal"] += subtotal
    else:
        carrinho.append(
            {
                "produto": produto,
                "tamanho": tamanho,
                "personalizado": is_personalizado,
                "nome_pers": nome_pers,
                "num_pers": num_pers,
                "quantidade": quantidade,
                "subtotal": subtotal,
            }
        )

    atualizar_carrinho()

    # Reset de campos
    campo_quantidade.delete(0, tk.END)
    campo_quantidade.insert(0, "1")
    var_personalizar.set(False)
    alternar_campos_personalizacao()

    messagebox.showinfo("Sucesso", "Camisa adicionada ao carrinho!")


def remover_carrinho():
    selecionado = lista_carrinho.selection()

    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione um item no carrinho para remover.")
        return

    indice = lista_carrinho.index(selecionado[0])
    carrinho.pop(indice)
    atualizar_carrinho()


def finalizar_pedido():
    if not carrinho:
        messagebox.showwarning("Aviso", "O carrinho está vazio.")
        return

    nome_cliente = campo_cliente.get().strip()

    if nome_cliente == "":
        messagebox.showwarning("Aviso", "Digite ou gere o nome do cliente.")
        return

    total = sum(item["subtotal"] for item in carrinho)
    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Gera um resumo descritivo de todos os itens comprados
    resumo_itens = []
    for item in carrinho:
        txt = f"{item['quantidade']}x {item['produto']} ({item['tamanho']})"
        if item["personalizado"]:
            txt += f" [Pers: {item['nome_pers']} nº{item['num_pers']}]"
        resumo_itens.append(txt)

    detalhes_str = " | ".join(resumo_itens)

    cursor.execute(
        """
        INSERT INTO pedidos (cliente, detalhes, total, data)
        VALUES (?, ?, ?, ?)
        """,
        (nome_cliente, detalhes_str, total, data),
    )

    conexao.commit()

    messagebox.showinfo(
        "Pedido Finalizado",
        f"Cliente: {nome_cliente}\n"
        f"Total: R$ {total:.2f}\n"
        f"Data: {data}\n\n"
        "Obrigado pela compra!",
    )

    carrinho.clear()
    atualizar_carrinho()
    campo_cliente.delete(0, tk.END)


def gerar_cliente():
    nome = fake.name()
    email = fake.email()

    campo_cliente.delete(0, tk.END)
    campo_cliente.insert(0, nome)

    cursor.execute(
        "INSERT INTO clientes (nome, email) VALUES (?, ?)", (nome, email)
    )
    conexao.commit()

    messagebox.showinfo("Cliente Gerado", f"Nome: {nome}\nEmail: {email}")


def mostrar_pedidos():
    janela_pedidos = tk.Toplevel(janela)
    janela_pedidos.title("Histórico de Pedidos")
    janela_pedidos.geometry("800x400")

    tabela_pedidos = ttk.Treeview(
        janela_pedidos,
        columns=("id", "cliente", "detalhes", "total", "data"),
        show="headings",
    )

    tabela_pedidos.heading("id", text="ID")
    tabela_pedidos.heading("cliente", text="Cliente")
    tabela_pedidos.heading("detalhes", text="Itens do Pedido")
    tabela_pedidos.heading("total", text="Total")
    tabela_pedidos.heading("data", text="Data")

    tabela_pedidos.column("id", width=40, anchor="center")
    tabela_pedidos.column("cliente", width=150)
    tabela_pedidos.column("detalhes", width=320)
    tabela_pedidos.column("total", width=100, anchor="center")
    tabela_pedidos.column("data", width=130, anchor="center")

    tabela_pedidos.pack(fill="both", expand=True, padx=10, pady=10)

    cursor.execute(
        "SELECT id, cliente, detalhes, total, data FROM pedidos ORDER BY id DESC"
    )
    for pedido in cursor.fetchall():
        tabela_pedidos.insert(
            "",
            "end",
            values=(
                pedido[0],
                pedido[1],
                pedido[2],
                f"R$ {pedido[3]:.2f}",
                pedido[4],
            ),
        )


def fechar_programa():
    conexao.close()
    janela.destroy()


# ==========================================
# DIVISÃO DA INTERFACE (DUAS COLUNAS)
# ==========================================

frame_esquerda = tk.Frame(janela, bg="white", padx=15, pady=15)
frame_esquerda.pack(side="left", fill="both", expand=True)

frame_direita = tk.Frame(janela, bg="#c62828", padx=15, pady=15)
frame_direita.pack(side="right", fill="both", expand=True)

# ==========================================
# LADO ESQUERDO: CATÁLOGOS E OPÇÕES DE TAMANHO
# ==========================================

tk.Label(
    frame_esquerda,
    text=NOME_LOJA,
    font=("Arial", 22, "bold"),
    bg="white",
    fg="#b71c1c",
).pack(anchor="w", pady=(0, 2))

tk.Label(
    frame_esquerda,
    text="Loja de Camisas de Times Brasileiros",
    font=("Arial", 11),
    bg="white",
    fg="#555555",
).pack(anchor="w", pady=(0, 10))

frame_produtos = tk.LabelFrame(
    frame_esquerda,
    text=" Camisas Disponíveis ",
    font=("Arial", 11, "bold"),
    bg="white",
    padx=10,
    pady=10,
)
frame_produtos.pack(fill="both", expand=True, pady=5)

tabela = ttk.Treeview(
    frame_produtos,
    columns=("numero", "produto", "preco"),
    show="headings",
    height=8,
)

tabela.heading("numero", text="Nº")
tabela.heading("produto", text="Camisa")
tabela.heading("preco", text="Preço Base (R$)")

tabela.column("numero", width=50, anchor="center")
tabela.column("produto", width=220)
tabela.column("preco", width=120, anchor="center")

barra = ttk.Scrollbar(frame_produtos, orient="vertical", command=tabela.yview)
tabela.configure(yscrollcommand=barra.set)

tabela.pack(side="left", fill="both", expand=True)
barra.pack(side="right", fill="y")

cursor.execute("SELECT id, nome, preco FROM produtos")
for produto in cursor.fetchall():
    tabela.insert("", "end", values=(produto[0], produto[1], f"{produto[2]:.2f}"))

# Painel de Opções da Camisa (Tamanho e Personalização)
frame_opcoes = tk.LabelFrame(
    frame_esquerda,
    text=" Opções da Camisa ",
    font=("Arial", 10, "bold"),
    bg="white",
    padx=10,
    pady=10,
)
frame_opcoes.pack(fill="x", pady=5)

# Tamanho + Quantidade
frame_linha1 = tk.Frame(frame_opcoes, bg="white")
frame_linha1.pack(fill="x", pady=2)

tk.Label(frame_linha1, text="Tamanho:", bg="white").pack(side="left", padx=(0, 5))
combo_tamanho = ttk.Combobox(
    frame_linha1, values=["PP", "P", "M", "G", "GG"], width=5, state="readonly"
)
combo_tamanho.set("M")
combo_tamanho.pack(side="left", padx=(0, 15))

tk.Label(frame_linha1, text="Quantidade:", bg="white").pack(
    side="left", padx=(0, 5)
)
campo_quantidade = tk.Entry(frame_linha1, width=5)
campo_quantidade.insert(0, "1")
campo_quantidade.pack(side="left")

# Checkbox e Entradas para Personalização
var_personalizar = tk.BooleanVar(value=False)
chk_personalizar = tk.Checkbutton(
    frame_opcoes,
    text=f"Personalizar Nome e Número (+R$ {PRECO_PERSONALIZACAO:.2f})",
    variable=var_personalizar,
    command=alternar_campos_personalizacao,
    bg="white",
    font=("Arial", 9, "bold"),
)
chk_personalizar.pack(anchor="w", pady=(8, 4))

frame_linha2 = tk.Frame(frame_opcoes, bg="white")
frame_linha2.pack(fill="x")

tk.Label(frame_linha2, text="Nome:", bg="white").pack(side="left", padx=(0, 5))
campo_nome_camisa = tk.Entry(frame_linha2, width=15, state="disabled")
campo_nome_camisa.pack(side="left", padx=(0, 10))

tk.Label(frame_linha2, text="Nº:", bg="white").pack(side="left", padx=(0, 5))
campo_numero_camisa = tk.Entry(frame_linha2, width=5, state="disabled")
campo_numero_camisa.pack(side="left")

# Botão Adicionar
botao_adicionar = tk.Button(
    frame_esquerda,
    text="Adicionar ao Carrinho",
    command=adicionar_carrinho,
    bg="#b71c1c",
    fg="white",
    font=("Arial", 11, "bold"),
    pady=6,
    cursor="hand2",
)
botao_adicionar.pack(fill="x", pady=10)

# ==========================================
# LADO DIREITO: CARRINHO E FINALIZAÇÃO
# ==========================================

tk.Label(
    frame_direita,
    text="CARRINHO & CHECKOUT",
    font=("Arial", 18, "bold"),
    bg="#c62828",
    fg="white",
).pack(anchor="w", pady=(0, 10))

frame_carrinho = tk.LabelFrame(
    frame_direita,
    text=" Itens Selecionados ",
    font=("Arial", 11, "bold"),
    bg="#c62828",
    fg="white",
    padx=10,
    pady=10,
)
frame_carrinho.pack(fill="both", expand=True, pady=5)

lista_carrinho = ttk.Treeview(
    frame_carrinho,
    columns=("produto", "tam", "pers", "qtd", "subtotal"),
    show="headings",
    height=6,
)

lista_carrinho.heading("produto", text="Produto")
lista_carrinho.heading("tam", text="Tam.")
lista_carrinho.heading("pers", text="Pers.")
lista_carrinho.heading("qtd", text="Qtd.")
lista_carrinho.heading("subtotal", text="Subtotal")

lista_carrinho.column("produto", width=160)
lista_carrinho.column("tam", width=45, anchor="center")
lista_carrinho.column("pers", width=45, anchor="center")
lista_carrinho.column("qtd", width=40, anchor="center")
lista_carrinho.column("subtotal", width=80, anchor="center")

lista_carrinho.pack(fill="both", expand=True)

botao_remover = tk.Button(
    frame_carrinho,
    text="Remover Item Selecionado",
    command=remover_carrinho,
    bg="#9a0007",
    fg="white",
    font=("Arial", 9, "bold"),
    cursor="hand2",
)
botao_remover.pack(pady=(8, 0))

label_total = tk.Label(
    frame_direita,
    text="Total: R$ 0.00",
    font=("Arial", 16, "bold"),
    bg="#c62828",
    fg="white",
)
label_total.pack(anchor="e", pady=8)

# Dados do Cliente
frame_cliente = tk.LabelFrame(
    frame_direita,
    text=" Dados do Cliente ",
    font=("Arial", 11, "bold"),
    bg="#c62828",
    fg="white",
    padx=10,
    pady=10,
)
frame_cliente.pack(fill="x", pady=5)

tk.Label(
    frame_cliente,
    text="Nome:",
    bg="#c62828",
    fg="white",
    font=("Arial", 10, "bold"),
).pack(anchor="w")

frame_input_cliente = tk.Frame(frame_cliente, bg="#c62828")
frame_input_cliente.pack(fill="x", pady=5)

campo_cliente = tk.Entry(frame_input_cliente, font=("Arial", 11))
campo_cliente.pack(side="left", fill="x", expand=True, padx=(0, 5))

botao_cliente = tk.Button(
    frame_input_cliente,
    text="Gerar Faker",
    command=gerar_cliente,
    bg="#7d3c98",
    fg="white",
    font=("Arial", 9, "bold"),
    cursor="hand2",
)
botao_cliente.pack(side="right")

# Ações Finais
frame_botoes_finais = tk.Frame(frame_direita, bg="#c62828", pady=5)
frame_botoes_finais.pack(fill="x")

botao_finalizar = tk.Button(
    frame_botoes_finais,
    text="FINALIZAR PEDIDO",
    command=finalizar_pedido,
    bg="#2e7d32",
    fg="white",
    font=("Arial", 12, "bold"),
    pady=8,
    cursor="hand2",
)
botao_finalizar.pack(fill="x", pady=(0, 5))

botao_historico = tk.Button(
    frame_botoes_finais,
    text="Histórico de Pedidos",
    command=mostrar_pedidos,
    bg="#333333",
    fg="white",
    font=("Arial", 10),
    cursor="hand2",
)
botao_historico.pack(fill="x")

janela.protocol("WM_DELETE_WINDOW", fechar_programa)
janela.mainloop()