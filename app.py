from datetime import datetime
import re
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# Dados iniciais para o dashboard já abrir visualmente rico para demonstração
monitored_products = [
    {
        "id": 1,
        "name": "Placa de Vídeo RX 6600 8GB GDDR6",
        "url": "https://exemplo.com/rx-6600",
        "current_price": 1349.90,
        "target_price": 1400.00,
        "previous_price": 1520.00,
        "last_checked": "Hoje, 08:30",
        "status": "below_target",
    },
    {
        "id": 2,
        "name": "Teclado Mecânico Switch Blue RGB",
        "url": "https://exemplo.com/teclado-mecanico",
        "current_price": 289.90,
        "target_price": 250.00,
        "previous_price": 289.90,
        "last_checked": "Hoje, 08:30",
        "status": "monitoring",
    },
    {
        "id": 3,
        "name": "Monitor Gamer 24'' 165Hz IPS",
        "url": "https://exemplo.com/monitor-165hz",
        "current_price": 879.00,
        "target_price": 900.00,
        "previous_price": 999.00,
        "last_checked": "Hoje, 08:30",
        "status": "below_target",
    },
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PricePulse AI | Monitor Inteligente de Preços</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased">

    <div class="max-w-5xl mx-auto px-6 py-10">
        <!-- Header -->
        <div class="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-800 pb-6 mb-8">
            <div>
                <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-purple-500 animate-pulse"></span>
                    <span class="text-xs uppercase tracking-widest text-purple-400 font-semibold">Web Scraping & Automação</span>
                </div>
                <h1 class="text-3xl font-bold mt-1 text-white">PricePulse <span class="text-purple-400">Monitor</span></h1>
                <p class="text-slate-400 text-sm mt-1">Rastreamento automatizado de preços e alertas de oportunidade em tempo real.</p>
            </div>
            <div class="mt-4 md:mt-0 flex gap-4 text-sm">
                <div class="bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg">
                    <span class="text-slate-400 block text-xs">Ativos</span>
                    <span class="font-bold text-lg text-white" id="total-count">{{ products|length }}</span>
                </div>
                <div class="bg-slate-900 border border-emerald-900/50 px-4 py-2 rounded-lg">
                    <span class="text-emerald-400 block text-xs">Em Alerta</span>
                    <span class="font-bold text-lg text-emerald-400" id="alert-count">
                        {{ products|selectattr('status', 'equalto', 'below_target')|list|length }}
                    </span>
                </div>
            </div>
        </div>

        <!-- Formulário de Adição -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-6 mb-8 shadow-xl">
            <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-300 mb-4">Adicionar Novo Monitoramento</h2>
            <form id="add-form" class="grid grid-cols-1 md:grid-cols-12 gap-4">
                <div class="md:col-span-5">
                    <label class="block text-xs text-slate-400 mb-1">URL do Produto (E-commerce)</label>
                    <input type="url" id="url" required placeholder="https://loja.com.br/produto"
                        class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500">
                </div>
                <div class="md:col-span-3">
                    <label class="block text-xs text-slate-400 mb-1">Nome (Opcional - auto-detecta)</label>
                    <input type="text" id="name" placeholder="Ex: SSD NVMe 1TB"
                        class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500">
                </div>
                <div class="md:col-span-2">
                    <label class="block text-xs text-slate-400 mb-1">Preço Alvo (R$)</label>
                    <input type="number" step="0.01" id="target_price" required placeholder="350.00"
                        class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500">
                </div>
                <div class="md:col-span-2 flex items-end">
                    <button type="submit" id="submit-btn"
                        class="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold py-2 px-4 rounded-lg text-sm transition cursor-pointer">
                        + Rastrear
                    </button>
                </div>
            </form>
        </div>

        <!-- Lista de Produtos -->
        <div id="product-list" class="space-y-4">
            {% for p in products %}
            <div class="bg-slate-900 border {% if p.status == 'below_target' %}border-emerald-500/40{% else %}border-slate-800{% endif %} rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 transition hover:border-slate-700" id="card-{{ p.id }}">
                <div>
                    <div class="flex items-center gap-2 mb-1">
                        {% if p.status == 'below_target' %}
                        <span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                            ● Alvo Atingido
                        </span>
                        {% else %}
                        <span class="bg-slate-800 text-slate-400 text-xs font-medium px-2.5 py-0.5 rounded-full">
                            Monitorando
                        </span>
                        {% endif %}
                        <span class="text-xs text-slate-500">Atualizado: {{ p.last_checked }}</span>
                    </div>
                    <h3 class="text-lg font-semibold text-white">{{ p.name }}</h3>
                    <a href="{{ p.url }}" target="_blank" class="text-xs text-purple-400 hover:underline truncate block max-w-md">{{ p.url }}</a>
                </div>

                <div class="flex items-center gap-6">
                    <div class="text-right">
                        <span class="text-xs text-slate-400 block">Preço Atual</span>
                        <span class="text-xl font-bold {% if p.status == 'below_target' %}text-emerald-400{% else %}text-white{% endif %}" id="price-{{ p.id }}">
                            R$ {{ "%.2f"|format(p.current_price) }}
                        </span>
                        <span class="text-xs text-slate-500 block">Alvo: R$ {{ "%.2f"|format(p.target_price) }}</span>
                    </div>

                    {% if p.status != 'below_target' %}
                    <button onclick="simulateDrop({{ p.id }})" title="Simular queda de preço no scraper"
                        class="bg-slate-800 hover:bg-purple-600/20 hover:text-purple-300 border border-slate-700 text-xs px-3 py-2 rounded-lg transition cursor-pointer">
                        Simular Queda
                    </button>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        document.getElementById('add-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submit-btn');
            btn.innerText = 'Extraindo...';
            btn.disabled = true;

            const payload = {
                url: document.getElementById('url').value,
                name: document.getElementById('name').value,
                target_price: document.getElementById('target_price').value
            };

            const res = await fetch('/api/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                window.location.reload();
            } else {
                btn.innerText = '+ Rastrear';
                btn.disabled = false;
            }
        });

        async function simulateDrop(id) {
            const res = await fetch(`/api/simulate-drop/${id}`, { method: 'POST' });
            if (res.ok) {
                window.location.reload();
            }
        }
    </script>
</body>
</html>
"""


def extract_product_info(url):
    """Tenta extrair título e preço real de uma URL pública."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = (
            soup.title.string.strip() if soup.title else "Produto Monitorado"
        )
        title = title[:65] + "..." if len(title) > 65 else title

        text = soup.get_text()
        brl_matches = re.findall(r"R\$\s?(\d{1,3}(?:\.\d{3})*,\d{2})", text)
        usd_matches = re.findall(r"\$\s?(\d{1,3}(?:,\d{3})*\.\d{2})", text)

        if brl_matches:
            raw_price = brl_matches[0].replace(".", "").replace(",", ".")
            return title, float(raw_price)
        elif usd_matches:
            raw_price = usd_matches[0].replace(",", "")
            return title, float(raw_price)

        return title, None
    except Exception:
        return None, None


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, products=monitored_products)


@app.route("/api/add", methods=["POST"])
def add_product():
    data = request.json
    url = data.get("url", "").strip()
    target_price = float(data.get("target_price", 0))
    manual_name = data.get("name", "").strip()
    manual_price = data.get("manual_price")

    scraped_title, scraped_price = extract_product_info(url)

    final_name = (
        manual_name or scraped_title or "Produto Personalizado (Monitorado)"
    )
    final_price = (
        float(manual_price)
        if manual_price
        else (scraped_price if scraped_price else target_price * 1.08)
    )

    status = "below_target" if final_price <= target_price else "monitoring"

    new_item = {
        "id": len(monitored_products) + 1,
        "name": final_name,
        "url": url,
        "current_price": round(final_price, 2),
        "target_price": round(target_price, 2),
        "previous_price": round(final_price * 1.05, 2),
        "last_checked": datetime.now().strftime("Hoje, %H:%M"),
        "status": status,
    }
    monitored_products.insert(0, new_item)
    return jsonify({"success": True, "product": new_item})


@app.route("/api/simulate-drop/<int:product_id>", methods=["POST"])
def simulate_drop(product_id):
    for p in monitored_products:
        if p["id"] == product_id:
            p["previous_price"] = p["current_price"]
            p["current_price"] = round(p["target_price"] * 0.92, 2)
            p["status"] = "below_target"
            p["last_checked"] = datetime.now().strftime("Agora (%H:%M)")
            return jsonify({"success": True, "product": p})
    return jsonify({"success": False}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)