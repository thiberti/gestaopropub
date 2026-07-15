// ==========================================
// 1. FUNÇÕES GERAIS (ORDENAÇÃO)
// ==========================================
// 1. ORDENAÇÃO UNIVERSAL
function sortTable(n, tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const tbody = table.querySelector('tbody') || table;
    const rows = Array.from(tbody.querySelectorAll('tr')).filter(r => r.style.display !== 'none');
    const dir = table.dataset.sortDir === 'asc' ? 'desc' : 'asc';
    table.dataset.sortDir = dir;
    table.dataset.sortCol = n;
    rows.sort((a, b) => {
        let x = (a.cells[n]?.innerText || '').trim();
        let y = (b.cells[n]?.innerText || '').trim();
        if (/r\$|#/.test(x.toLowerCase())) {
            x = parseFloat(x.replace(/[r$\s#.]/gi, '').replace(',', '.')) || 0;
            y = parseFloat(y.replace(/[r$\s#.]/gi, '').replace(',', '.')) || 0;
        } else if (validarData(x) && validarData(y)) {
            x = transformarParaData(x); y = transformarParaData(y);
        } else if (!isNaN(parseFloat(x))) {
            x = parseFloat(x); y = parseFloat(y);
        } else {
            x = x.toLowerCase(); y = y.toLowerCase();
        }
        return dir === 'asc' ? (x > y ? 1 : -1) : (x < y ? 1 : -1);
    });
    rows.forEach(r => tbody.appendChild(r));
}
function validarData(v) { return v.includes('/') || (v.includes('-') && v.length >= 8); }
function transformarParaData(v) {
    if (v.includes('-')) return new Date(v).getTime();
    const p = v.split('/'); return new Date(p[2], p[1] - 1, p[0]).getTime();
}

// 2. MÁSCARA DE TELEFONE
function phoneMask(v) {
    v = v.replace(/\D/g, "");
    if (v.length > 11) v = v.slice(0, 11);
    if (v.length > 10) v = v.replace(/^(\d{2})(\d{5})(\d{4})/, "($1) $2-$3");
    else v = v.replace(/^(\d{2})(\d{4})(\d{4})/, "($1) $2-$3");
    return v;
}
document.addEventListener("DOMContentLoaded", () => {
    document.body.addEventListener("input", (e) => {
        if (e.target.classList.contains("tel-mask")) e.target.value = phoneMask(e.target.value);
    });
});
// ==========================================
// 3. FUNÇÕES DE CLIENTES E ESTOQUE (MODAIS)
// ==========================================
// 3. MODAIS (CLIENTES, ESTOQUE, FINANCEIRO)
function abrirEditarCliente(id, nome, tel, nasc) {
    document.getElementById('formEditarCliente').action = '/editar_cliente/' + id;
    document.getElementById('edit_nome_cli').value = nome;
    document.getElementById('edit_tel_cli').value = tel;
    const nascEl = document.getElementById('edit_nasc_cli');
    if (nascEl) nascEl.value = nasc || '';
    new bootstrap.Modal(document.getElementById('modalEditarCliente')).show();
}
function abrirEditarEstoque(id, nome, marca, linha, sku, preco, qtd) {
    document.getElementById('formEditarProduto').action = '/editar_produto/' + id;
    document.getElementById('edit_nome').value = nome;
    document.getElementById('edit_marca').value = marca;
    document.getElementById('edit_linha').value = linha;
    document.getElementById('edit_sku').value = sku;
    document.getElementById('edit_preco').value = preco;
    document.getElementById('edit_quantidade').value = qtd;
    new bootstrap.Modal(document.getElementById('modalEditarProduto')).show();
}
function abrirEditarFinanceiro(id, desc, valor, tipo, venc) {
    document.getElementById('formEditarFinanceiro').action = '/editar_financeiro/' + id;
    document.getElementById('edit_fin_desc').value = desc;
    document.getElementById('edit_fin_valor').value = valor;
    document.getElementById('edit_fin_tipo').value = tipo;
    document.getElementById('edit_fin_venc').value = venc;
    new bootstrap.Modal(document.getElementById('modalEditarFinanceiro')).show();
}

// ==========================================
// 4. FUNÇÕES DE VENDAS (LÓGICA DO GRID)
// ==========================================
let itensCarrinho = [];
let somenteLeitura = false;

function novoPedido() {
    somenteLeitura = false;
    document.getElementById('formVenda').reset();
    document.getElementById('formVenda').action = "/vendas";
    document.getElementById('modalTitulo').innerText = "Novo Pedido";
    document.getElementById('bloco_data_pagamento').style.display = 'none';
    alternarTravaCampos(false);
    document.getElementById('campo_emissao').valueAsDate = new Date();
    itensCarrinho = []; adicionarLinhaVazia();
    new bootstrap.Modal(document.getElementById('modalPedido')).show();
}

function abrirVenda(id, viewOnly) {
    somenteLeitura = viewOnly;
    const v = vendasBase.find(x => x.id === id);
    if (!v) return;
    document.getElementById('formVenda').action = "/editar_venda/" + id;
    document.getElementById('modalTitulo').innerText = "Pedido #" + v.numero_pedido;
    document.getElementById('campo_cliente').value = v.cliente;
    document.getElementById('campo_emissao').value = v.data_emissao;
    document.getElementById('campo_vencimento').value = v.vencimento;
    document.getElementById('campo_parcelas').value = v.parcelas;
    document.getElementById('campo_forma').value = v.forma_pagamento;
    document.getElementById('campo_obs').value = v.observacao;
    document.getElementById('desc_total_pedido').value = v.desconto_total_percent;
    if (v.status === 'pago' && v.data_pagamento) {
        document.getElementById('bloco_data_pagamento').style.display = 'block';
        document.getElementById('campo_data_pagamento').value = v.data_pagamento;
    } else { document.getElementById('bloco_data_pagamento').style.display = 'none'; }
    itensCarrinho = v.itens;
    renderizarTabelaVendas();
    alternarTravaCampos(viewOnly);
    new bootstrap.Modal(document.getElementById('modalPedido')).show();
}

function alternarTravaCampos(travar) {
    document.querySelectorAll('#formVenda input, #formVenda select, #formVenda textarea').forEach(i => i.disabled = travar);
    document.getElementById('btnNovaLinha').style.display = travar ? 'none' : 'block';
    document.getElementById('btnFinalizar').style.display = travar ? 'none' : 'block';
}

function adicionarLinhaVazia() {
    itensCarrinho.push({ id: '', sku: '', nome: '', preco: 0, quantidade: 1, desconto: 0, total: 0 });
    renderizarTabelaVendas();
}

function renderizarTabelaVendas() {
    const body = document.getElementById('grid_itens'); body.innerHTML = "";
    let bruto = 0;
    itensCarrinho.forEach((item, i) => {
        const sub = (item.preco * item.quantidade) * (1 - item.desconto / 100);
        bruto += sub;
        body.innerHTML += `<tr>
            <td>
    <div class="input-group input-group-sm">
        <button type="button" class="btn btn-outline-secondary" onclick="abrirBusca(${i})" ${somenteLeitura ? 'disabled' : ''}>
            <i class="bi bi-folder-fill"></i>
        </button>
        <input type="text" class="grid-input ps-2" value="${item.sku}" onchange="buscarSKU(${i}, this.value)" ${somenteLeitura ? 'disabled' : ''} style="width: 80px;">
    </div>
</td>
            <td><input type="text" class="grid-input" value="${item.nome}" readonly></td>
            <td><input type="number" class="grid-input text-center" value="${item.quantidade}" onchange="atualizarItemVenda(${i},'quantidade',this.value)" ${somenteLeitura ? 'disabled' : ''}></td>
            <td><input type="number" class="grid-input" value="${item.preco}" onchange="atualizarItemVenda(${i},'preco',this.value)" ${somenteLeitura ? 'disabled' : ''}></td>
            <td><input type="number" class="grid-input text-center" value="${item.desconto}" onchange="atualizarItemVenda(${i},'desconto',this.value)" ${somenteLeitura ? 'disabled' : ''}></td>
            <td class="text-end fw-bold">R$ ${sub.toFixed(2)}</td>
            <td class="text-center"><button type="button" class="btn btn-sm text-danger" onclick="removerItemVenda(${i})" style="display:${somenteLeitura ? 'none' : ''}"><i class="bi bi-trash-fill"></i></button></td>
        </tr>`;
    });
    const descG = parseFloat(document.getElementById('desc_total_pedido').value) || 0;
    const total = bruto * (1 - descG / 100);
    document.getElementById('total_display').innerText = "R$ " + total.toFixed(2);
    document.getElementById('total_geral_input').value = total.toFixed(2);
    document.getElementById('itens_venda_json').value = JSON.stringify(itensCarrinho.filter(x => x.id !== ''));
}

function buscarSKU(i, sku) {
    const p = produtosBase.find(x => x.sku === sku);
    if (p) { itensCarrinho[i] = { ...itensCarrinho[i], id: p.id, sku: p.sku, nome: p.nome, preco: p.preco }; renderizarTabelaVendas(); }
}
function atualizarItemVenda(i, c, v) { itensCarrinho[i][c] = parseFloat(v); renderizarTabelaVendas(); }
function removerItemVenda(i) { itensCarrinho.splice(i, 1); if (!itensCarrinho.length) adicionarLinhaVazia(); renderizarTabelaVendas(); }

let indexBuscaAtual = -1;
function abrirBusca(index) {
    indexBuscaAtual = index;
    new bootstrap.Modal(document.getElementById('modalBuscaProduto')).show();
}
function selecionarDaBusca(sku) {
    buscarSKU(indexBuscaAtual, sku);
    bootstrap.Modal.getInstance(document.getElementById('modalBuscaProduto')).hide();
}
function filtrarBuscaVendas() {
    let f = document.getElementById("inputBuscaFiltro").value.toLowerCase();
    document.querySelectorAll(".item-busca").forEach(r => r.style.display = r.innerText.toLowerCase().includes(f) ? "" : "none");
}

function aplicarFiltrosEstoque() {
    const n = document.getElementById("filterNome").value.toLowerCase();
    const m = document.getElementById("filterMarca").value.toLowerCase();
    const l = document.getElementById("filterLinha").value.toLowerCase();
    const s = document.getElementById("filterSKU").value.toLowerCase();
    const limite = parseInt(document.getElementById("limitarLinhas").value);

    const rows = document.querySelectorAll("#corpoTabela tr");
    let visiveis = 0;

    rows.forEach(row => {
        const txt = row.innerText.toLowerCase();
        const passa = txt.includes(n) && txt.includes(m) && txt.includes(l) && txt.includes(s);

        if (passa && (limite === 0 || visiveis < limite)) {
            row.style.display = "";
            visiveis++;
        } else {
            row.style.display = "none";
        }
    });

    const total = document.querySelectorAll("#corpoTabela tr").length;
    const label = document.getElementById("labelContagem");
    if (label) label.textContent = `Exibindo ${visiveis} de ${total} produtos`;
}

function limparFiltrosEstoque() {
    document.getElementById("filterNome").value = "";
    document.getElementById("filterMarca").value = "";
    document.getElementById("filterLinha").value = "";
    document.getElementById("filterSKU").value = "";
    aplicarFiltrosEstoque();
}

aplicarFiltrosEstoque();