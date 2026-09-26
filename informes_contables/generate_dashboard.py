#!/usr/bin/env python3
"""
Financial Dashboard Generator for Cardales Club

Reads Excel files from data/{year}/{month}/ and generates an interactive HTML dashboard.
"""

import argparse
import os
import webbrowser
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def find_excel_files(data_dir: Path) -> Dict[str, Path]:
    """Auto-discover Excel files in the data directory based on content patterns."""
    files = {}
    for f in data_dir.glob("*.xlsx"):
        df = pd.read_excel(f, nrows=30)
        text = df.to_string().lower()
        
        if "saldo de caja" in text or "cobranza bancaria" in text:
            files["cashflow"] = f
        elif "deudores" in text and "socio" in text:
            files["debtors"] = f
        elif "erogaciones" in text or ("rubro" in text and "cuit" in text):
            files["expenses"] = f
        elif "depositos bancarios no identificados" in text:
            files["deposits"] = f
    
    return files


def load_cashflow(filepath: Path) -> Dict[str, Any]:
    """Load and parse cash flow data."""
    df = pd.read_excel(filepath)
    
    result = {
        "opening_balance": 0,
        "closing_balance": 0,
        "surplus_deficit": 0,
        "total_collections": 0,
        "collection_channels": {},
        "total_income": 0,
    }
    
    for i, row in df.iterrows():
        for j, val in enumerate(row):
            if pd.isna(val):
                continue
            val_str = str(val)
            
            if "Saldo de Caja al 01" in val_str:
                result["opening_balance"] = float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0
            elif "Saldo de Caja al 30" in val_str:
                result["closing_balance"] = float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0
            elif "Superavit / Deficit" in val_str:
                result["surplus_deficit"] = float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0
            elif "Total Cobranza Bancaria" in val_str:
                result["total_collections"] = float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0
            elif "Total Ingresos de Fondos" in val_str:
                result["total_income"] = float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0
            elif j == 3 and pd.notna(row.iloc[5]):
                channel_name = val_str.strip()
                try:
                    amount = float(row.iloc[5])
                    if amount > 0 and channel_name and not channel_name.startswith("Unnamed"):
                        result["collection_channels"][channel_name] = amount
                except (ValueError, TypeError):
                    pass
    
    return result


def load_debtors(filepath: Path) -> pd.DataFrame:
    """Load and parse debtors data."""
    df = pd.read_excel(filepath)
    
    header_row = None
    for i, row in df.iterrows():
        if any("SOCIO" in str(v) for v in row if pd.notna(v)):
            header_row = i
            break
    
    if header_row is None:
        return pd.DataFrame()
    
    columns = ["socio", "uf", "nombre", "abr_26", "mar_26", "feb_26", "ene_26", 
               "dic_25", "nov_25", "oct_25", "deuda_anterior", "total_deuda"]
    
    data_rows = []
    for i, row in df.iloc[header_row + 1:].iterrows():
        if pd.notna(row.iloc[2]) and str(row.iloc[2]).strip() and "-" in str(row.iloc[2]):
            row_data = {
                "socio": str(row.iloc[2]).strip(),
                "uf": str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "",
                "nombre": str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else "",
            }
            for k, col in enumerate(["abr_26", "mar_26", "feb_26", "ene_26", 
                                      "dic_25", "nov_25", "oct_25", "deuda_anterior", "total_deuda"]):
                try:
                    row_data[col] = float(row.iloc[5 + k]) if pd.notna(row.iloc[5 + k]) else 0
                except (ValueError, TypeError):
                    row_data[col] = 0
            data_rows.append(row_data)
    
    return pd.DataFrame(data_rows)


def load_expenses(filepath: Path) -> pd.DataFrame:
    """Load and parse expenses data."""
    df = pd.read_excel(filepath)
    
    header_row = None
    for i, row in df.iterrows():
        if any("Rubro" in str(v) for v in row if pd.notna(v)):
            header_row = i
            break
    
    if header_row is None:
        return pd.DataFrame()
    
    skip_patterns = ["total general", "total", "subtotal"]
    
    data_rows = []
    for i, row in df.iloc[header_row + 1:].iterrows():
        if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip():
            rubro = str(row.iloc[0]).strip()
            if any(pattern in rubro.lower() for pattern in skip_patterns):
                continue
            try:
                total = float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0
                if total > 0:
                    data_rows.append({
                        "rubro": rubro,
                        "descripcion": str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else "",
                        "detalle": str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "",
                        "empresa": str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "",
                        "cuit": str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else "",
                        "factura": str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else "",
                        "total": total,
                    })
            except (ValueError, TypeError):
                pass
    
    return pd.DataFrame(data_rows)


def load_deposits(filepath: Path) -> pd.DataFrame:
    """Load and parse unidentified deposits data."""
    df = pd.read_excel(filepath)
    
    data_rows = []
    current_bank = ""
    
    for i, row in df.iterrows():
        row_text = " ".join(str(v) for v in row if pd.notna(v))
        
        if "Banco Provincia" in row_text:
            current_bank = "Banco Provincia"
        elif "Banco Santander" in row_text:
            current_bank = "Banco Santander Rio"
        elif pd.notna(row.iloc[1]) and pd.notna(row.iloc[4]):
            try:
                fecha = row.iloc[1]
                if hasattr(fecha, 'strftime'):
                    fecha_str = fecha.strftime("%Y-%m-%d")
                else:
                    fecha_str = str(fecha)[:10]
                
                if fecha_str.startswith("20"):
                    importe = float(row.iloc[4]) if pd.notna(row.iloc[4]) else 0
                    if importe > 0:
                        data_rows.append({
                            "banco": current_bank,
                            "fecha": fecha_str,
                            "descripcion": str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "",
                            "importe": importe,
                        })
            except (ValueError, TypeError):
                pass
    
    return pd.DataFrame(data_rows)


def format_currency(value: float) -> str:
    """Format number as Argentine Pesos."""
    if abs(value) >= 1_000_000:
        return f"${value/1_000_000:,.2f}M"
    elif abs(value) >= 1_000:
        return f"${value/1_000:,.1f}K"
    return f"${value:,.2f}"


def create_summary_cards(cashflow: Dict, debtors: pd.DataFrame, 
                         expenses: pd.DataFrame, deposits: pd.DataFrame) -> str:
    """Generate HTML for summary cards."""
    total_debt = debtors["total_deuda"].sum() if not debtors.empty else 0
    total_expenses = expenses["total"].sum() if not expenses.empty else 0
    total_deposits = deposits["importe"].sum() if not deposits.empty else 0
    
    surplus_class = "positive" if cashflow["surplus_deficit"] >= 0 else "negative"
    surplus_sign = "+" if cashflow["surplus_deficit"] >= 0 else ""
    
    cards = f"""
    <div class="summary-cards">
        <div class="card">
            <div class="card-label">Saldo Inicial (01/04)</div>
            <div class="card-value">{format_currency(cashflow["opening_balance"])}</div>
        </div>
        <div class="card">
            <div class="card-label">Saldo Final (30/04)</div>
            <div class="card-value">{format_currency(cashflow["closing_balance"])}</div>
        </div>
        <div class="card {surplus_class}">
            <div class="card-label">Superávit/Déficit</div>
            <div class="card-value">{surplus_sign}{format_currency(cashflow["surplus_deficit"])}</div>
        </div>
        <div class="card">
            <div class="card-label">Cobranza Total</div>
            <div class="card-value">{format_currency(cashflow["total_collections"])}</div>
        </div>
        <div class="card">
            <div class="card-label">Erogaciones</div>
            <div class="card-value">{format_currency(total_expenses)}</div>
        </div>
        <div class="card warning">
            <div class="card-label">Deuda Total</div>
            <div class="card-value">{format_currency(total_debt)}</div>
        </div>
        <div class="card warning">
            <div class="card-label">Depósitos No Identificados</div>
            <div class="card-value">{format_currency(total_deposits)}</div>
        </div>
    </div>
    """
    return cards


def create_collections_chart(cashflow: Dict) -> str:
    """Create collections by channel bar chart."""
    channels = cashflow["collection_channels"]
    if not channels:
        return "<p>No hay datos de canales de cobranza</p>"
    
    sorted_channels = sorted(channels.items(), key=lambda x: x[1], reverse=True)
    names = [c[0] for c in sorted_channels]
    values = [float(c[1]) for c in sorted_channels]
    
    fig = go.Figure(go.Bar(
        x=values,
        y=names,
        orientation='h',
        marker_color='#3498db',
        text=[format_currency(v) for v in values],
        textposition='outside',
    ))
    
    fig.update_layout(
        title="Cobranza por Canal de Pago",
        xaxis_title="Monto ($)",
        yaxis_title="",
        height=400,
        margin=dict(l=200, r=100, t=50, b=50),
        xaxis=dict(tickformat=",.0f"),
    )
    
    return fig.to_html(full_html=False, include_plotlyjs=False)


def create_debtors_chart(debtors: pd.DataFrame) -> str:
    """Create top debtors bar chart."""
    if debtors.empty:
        return "<p>No hay datos de deudores</p>"
    
    top_debtors = debtors.nlargest(10, "total_deuda")
    
    fig = go.Figure(go.Bar(
        x=[float(v) for v in top_debtors["total_deuda"]],
        y=list(top_debtors["nombre"]),
        orientation='h',
        marker_color='#e74c3c',
        text=[format_currency(v) for v in top_debtors["total_deuda"]],
        textposition='outside',
    ))
    
    fig.update_layout(
        title="Top 10 Deudores",
        xaxis_title="Deuda Total ($)",
        yaxis_title="",
        height=400,
        margin=dict(l=250, r=100, t=50, b=50),
        xaxis=dict(tickformat=",.0f"),
    )
    
    return fig.to_html(full_html=False, include_plotlyjs=False)


def create_debtors_aging_chart(debtors: pd.DataFrame) -> str:
    """Create debt aging stacked bar chart."""
    if debtors.empty:
        return ""
    
    top_debtors = debtors.nlargest(10, "total_deuda")
    
    months = [
        ("abr_26", "Abril 26"),
        ("mar_26", "Marzo 26"),
        ("feb_26", "Febrero 26"),
        ("ene_26", "Enero 26"),
        ("dic_25", "Diciembre 25"),
        ("nov_25", "Noviembre 25"),
        ("oct_25", "Octubre 25"),
        ("deuda_anterior", "Períodos Anteriores"),
    ]
    
    colors = ['#3498db', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c', '#9b59b6', '#1abc9c', '#95a5a6']
    
    fig = go.Figure()
    
    for (col, label), color in zip(months, colors):
        fig.add_trace(go.Bar(
            name=label,
            y=list(top_debtors["nombre"]),
            x=[float(v) for v in top_debtors[col]],
            orientation='h',
            marker_color=color,
        ))
    
    fig.update_layout(
        title="Antigüedad de Deuda - Top 10 Deudores",
        barmode='stack',
        xaxis_title="Monto ($)",
        yaxis_title="",
        height=450,
        margin=dict(l=250, r=50, t=50, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    
    return fig.to_html(full_html=False, include_plotlyjs=False)


def create_expenses_pie_chart(expenses: pd.DataFrame) -> str:
    """Create expenses by category pie chart."""
    if expenses.empty:
        return "<p>No hay datos de erogaciones</p>"
    
    by_rubro = expenses.groupby("rubro")["total"].sum().sort_values(ascending=False)
    
    top_rubros = by_rubro.head(8)
    if len(by_rubro) > 8:
        otros = by_rubro.iloc[8:].sum()
        top_rubros = pd.concat([top_rubros, pd.Series({"Otros": otros})])
    
    short_labels = [label[:35] + "..." if len(label) > 35 else label for label in top_rubros.index]
    
    fig = go.Figure(go.Pie(
        labels=short_labels,
        values=[float(v) for v in top_rubros.values],
        textinfo='percent',
        textposition='inside',
        hole=0.3,
        hovertemplate="<b>%{label}</b><br>%{value:$,.0f}<br>%{percent}<extra></extra>",
    ))
    
    fig.update_layout(
        title="Erogaciones por Rubro",
        height=550,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=10),
        ),
    )
    
    return fig.to_html(full_html=False, include_plotlyjs=False)


def create_expenses_bar_chart(expenses: pd.DataFrame) -> str:
    """Create top expenses by category bar chart."""
    if expenses.empty:
        return ""
    
    by_rubro = expenses.groupby("rubro")["total"].sum().sort_values(ascending=True).tail(10)
    
    fig = go.Figure(go.Bar(
        x=[float(v) for v in by_rubro.values],
        y=list(by_rubro.index),
        orientation='h',
        marker_color='#9b59b6',
        text=[format_currency(v) for v in by_rubro.values],
        textposition='outside',
    ))
    
    fig.update_layout(
        title="Top 10 Rubros de Erogaciones",
        xaxis_title="Monto Total ($)",
        yaxis_title="",
        height=400,
        margin=dict(l=350, r=100, t=50, b=50),
    )
    
    return fig.to_html(full_html=False, include_plotlyjs=False)


def create_debtors_table(debtors: pd.DataFrame) -> str:
    """Create HTML table for all debtors."""
    if debtors.empty:
        return "<p>No hay datos de deudores</p>"
    
    sorted_df = debtors.sort_values("total_deuda", ascending=False)
    
    rows = ""
    for _, row in sorted_df.iterrows():
        rows += f"""
        <tr>
            <td>{row['socio']}</td>
            <td>{row['nombre']}</td>
            <td>{row['uf']}</td>
            <td class="number">{format_currency(row['abr_26'])}</td>
            <td class="number">{format_currency(row['mar_26'])}</td>
            <td class="number">{format_currency(row['feb_26'])}</td>
            <td class="number total">{format_currency(row['total_deuda'])}</td>
        </tr>
        """
    
    return f"""
    <div class="table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Socio</th>
                    <th>Nombre</th>
                    <th>UF</th>
                    <th>Abril 26</th>
                    <th>Marzo 26</th>
                    <th>Febrero 26</th>
                    <th>Total Deuda</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """


def create_deposits_table(deposits: pd.DataFrame) -> str:
    """Create HTML table for unidentified deposits."""
    if deposits.empty:
        return "<p>No hay depósitos sin identificar</p>"
    
    total = deposits["importe"].sum()
    
    rows = ""
    for _, row in deposits.iterrows():
        rows += f"""
        <tr>
            <td>{row['banco']}</td>
            <td>{row['fecha']}</td>
            <td>{row['descripcion'][:60]}...</td>
            <td class="number">{format_currency(row['importe'])}</td>
        </tr>
        """
    
    return f"""
    <div class="deposits-summary">
        <strong>Total sin identificar: {format_currency(total)}</strong> ({len(deposits)} depósitos)
    </div>
    <div class="table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Banco</th>
                    <th>Fecha</th>
                    <th>Descripción</th>
                    <th>Importe</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """


def create_expenses_table(expenses: pd.DataFrame) -> str:
    """Create HTML table for top expenses."""
    if expenses.empty:
        return "<p>No hay datos de erogaciones</p>"
    
    top_expenses = expenses.nlargest(20, "total")
    
    rows = ""
    for _, row in top_expenses.iterrows():
        rows += f"""
        <tr>
            <td>{row['rubro'][:40]}</td>
            <td>{row['descripcion'][:30]}</td>
            <td>{row['empresa'][:25]}</td>
            <td class="number">{format_currency(row['total'])}</td>
        </tr>
        """
    
    return f"""
    <div class="table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Rubro</th>
                    <th>Descripción</th>
                    <th>Empresa</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """


def generate_html(cashflow: Dict, debtors: pd.DataFrame, 
                  expenses: pd.DataFrame, deposits: pd.DataFrame,
                  period: str) -> str:
    """Generate the complete HTML dashboard."""
    
    summary_cards = create_summary_cards(cashflow, debtors, expenses, deposits)
    collections_chart = create_collections_chart(cashflow)
    debtors_chart = create_debtors_chart(debtors)
    debtors_aging = create_debtors_aging_chart(debtors)
    debtors_table = create_debtors_table(debtors)
    expenses_pie = create_expenses_pie_chart(expenses)
    expenses_bar = create_expenses_bar_chart(expenses)
    expenses_table = create_expenses_table(expenses)
    deposits_table = create_deposits_table(deposits)
    
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Financiero - {period}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f6fa;
            color: #2c3e50;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .header .period {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            text-align: center;
        }}
        
        .card-label {{
            font-size: 0.85rem;
            color: #7f8c8d;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .card-value {{
            font-size: 1.4rem;
            font-weight: 700;
            color: #2c3e50;
        }}
        
        .card.positive .card-value {{
            color: #27ae60;
        }}
        
        .card.negative .card-value {{
            color: #e74c3c;
        }}
        
        .card.warning {{
            border-left: 4px solid #f39c12;
        }}
        
        .section {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }}
        
        .section h2 {{
            font-size: 1.3rem;
            color: #2c3e50;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #ecf0f1;
        }}
        
        .tabs {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 0.5rem;
        }}
        
        .tab {{
            padding: 0.5rem 1rem;
            background: #ecf0f1;
            border: none;
            border-radius: 6px 6px 0 0;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }}
        
        .tab:hover {{
            background: #3498db;
            color: white;
        }}
        
        .tab.active {{
            background: #3498db;
            color: white;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 1.5rem;
        }}
        
        .table-container {{
            overflow-x: auto;
            max-height: 500px;
            overflow-y: auto;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        
        .data-table th {{
            background: #3498db;
            color: white;
            padding: 0.75rem;
            text-align: left;
            position: sticky;
            top: 0;
        }}
        
        .data-table td {{
            padding: 0.6rem 0.75rem;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .data-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .data-table .number {{
            text-align: right;
            font-family: 'Monaco', 'Consolas', monospace;
        }}
        
        .data-table .total {{
            font-weight: 700;
            color: #e74c3c;
        }}
        
        .deposits-summary {{
            background: #fff3cd;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            color: #856404;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #7f8c8d;
            font-size: 0.85rem;
        }}
        
        @media (max-width: 768px) {{
            .grid-2 {{
                grid-template-columns: 1fr;
            }}
            .summary-cards {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dashboard Financiero - Club Cardales</h1>
        <div class="period">{period}</div>
    </div>
    
    <div class="container">
        {summary_cards}
        
        <div class="section">
            <h2>Flujo de Caja - Cobranza por Canal</h2>
            {collections_chart}
        </div>
        
        <div class="section">
            <h2>Deudores</h2>
            <div class="tabs">
                <button class="tab active" onclick="showTab('debtors', 'chart')">Gráfico Top 10</button>
                <button class="tab" onclick="showTab('debtors', 'aging')">Antigüedad</button>
                <button class="tab" onclick="showTab('debtors', 'table')">Tabla Completa</button>
            </div>
            <div id="debtors-chart" class="tab-content active">
                {debtors_chart}
            </div>
            <div id="debtors-aging" class="tab-content">
                {debtors_aging}
            </div>
            <div id="debtors-table" class="tab-content">
                {debtors_table}
            </div>
        </div>
        
        <div class="section">
            <h2>Erogaciones</h2>
            <div class="tabs">
                <button class="tab active" onclick="showTab('expenses', 'pie')">Por Rubro</button>
                <button class="tab" onclick="showTab('expenses', 'bar')">Top 10</button>
                <button class="tab" onclick="showTab('expenses', 'table')">Detalle</button>
            </div>
            <div id="expenses-pie" class="tab-content active">
                {expenses_pie}
            </div>
            <div id="expenses-bar" class="tab-content">
                {expenses_bar}
            </div>
            <div id="expenses-table" class="tab-content">
                {expenses_table}
            </div>
        </div>
        
        <div class="section">
            <h2>Depósitos Bancarios No Identificados</h2>
            {deposits_table}
        </div>
    </div>
    
    <div class="footer">
        Generado automáticamente | Datos actualizados al cierre del período
    </div>
    
    <script>
        function showTab(section, tab) {{
            const tabs = document.querySelectorAll(`#${{section}}-chart, #${{section}}-aging, #${{section}}-table, #${{section}}-pie, #${{section}}-bar`);
            tabs.forEach(t => t && t.classList.remove('active'));
            
            const buttons = document.querySelectorAll(`.section:has(#${{section}}-${{tab}}) .tab`);
            buttons.forEach(b => b.classList.remove('active'));
            
            const content = document.getElementById(`${{section}}-${{tab}}`);
            if (content) {{
                content.classList.add('active');
                const allTabs = content.parentElement.querySelectorAll('.tab');
                const allContents = content.parentElement.querySelectorAll('.tab-content');
                allTabs.forEach(t => t.classList.remove('active'));
                allContents.forEach(c => c.classList.remove('active'));
                content.classList.add('active');
                
                const buttons = content.parentElement.querySelectorAll('.tab');
                buttons.forEach((btn, i) => {{
                    const contents = content.parentElement.querySelectorAll('.tab-content');
                    if (contents[i] === content) {{
                        btn.classList.add('active');
                    }}
                }});
            }}
        }}
    </script>
</body>
</html>
    """
    
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate financial dashboard from Excel files")
    parser.add_argument("--year", default="2026", help="Year (default: 2026)")
    parser.add_argument("--month", default="abr", help="Month abbreviation (default: abr)")
    parser.add_argument("--no-open", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()
    
    data_dir = Path(f"data/{args.year}/{args.month}")
    
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        return 1
    
    print(f"Looking for Excel files in {data_dir}...")
    files = find_excel_files(data_dir)
    
    if not files:
        print("Error: No Excel files found or could not identify file types")
        return 1
    
    print(f"Found files: {list(files.keys())}")
    
    print("Loading cash flow data...")
    cashflow = load_cashflow(files["cashflow"]) if "cashflow" in files else {}
    
    print("Loading debtors data...")
    debtors = load_debtors(files["debtors"]) if "debtors" in files else pd.DataFrame()
    
    print("Loading expenses data...")
    expenses = load_expenses(files["expenses"]) if "expenses" in files else pd.DataFrame()
    
    print("Loading deposits data...")
    deposits = load_deposits(files["deposits"]) if "deposits" in files else pd.DataFrame()
    
    month_names = {
        "ene": "Enero", "feb": "Febrero", "mar": "Marzo", "abr": "Abril",
        "may": "Mayo", "jun": "Junio", "jul": "Julio", "ago": "Agosto",
        "sep": "Septiembre", "oct": "Octubre", "nov": "Noviembre", "dic": "Diciembre"
    }
    period = f"{month_names.get(args.month, args.month)} {args.year}"
    
    print("Generating dashboard HTML...")
    html = generate_html(cashflow, debtors, expenses, deposits, period)
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"dashboard_{args.month}_{args.year}.html"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Dashboard saved to: {output_file}")
    
    if not args.no_open:
        abs_path = output_file.resolve()
        print(f"Opening in browser: file://{abs_path}")
        webbrowser.open(f"file://{abs_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
