
# Dashboard de Estoque - XLS diário

Projeto pronto para rodar localmente com **Streamlit + SQLite**.

## O que ele faz
- recebe **1 arquivo XLS/XLSX por dia**
- lê a aba `FJ Sistemas`
- usa cabeçalho na **linha 4**
- classifica os itens em:
  - CONGELADO
  - RESFRIADO
  - AMBIENTE
- compara com a capacidade cadastrada por filial
- grava histórico em banco local SQLite
- mostra dashboard interativo

## Estrutura do projeto
```bash
dashboard_estoque_xls/
├── app.py
├── requirements.txt
├── data/
│   ├── capacidades.csv
│   ├── mapa_grupos.csv
│   └── estoque.db   # será criado automaticamente
├── pages/
│   ├── 1_Upload.py
│   ├── 2_Dashboard.py
│   ├── 3_Capacidades.py
│   └── 4_Mapa_de_Grupos.py
└── services/
    ├── database.py
    ├── excel_reader.py
    ├── rules.py
    └── transform.py
```

## Como rodar
No terminal, entre na pasta do projeto e rode:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Como usar
1. Abra o menu lateral do Streamlit
2. Vá em **1_Upload**
3. Suba o arquivo do dia
4. Clique em **Processar arquivo**
5. Vá em **2_Dashboard**

## Onde ajustar as capacidades
Na página **3_Capacidades**.

## Onde ajustar as regras dos grupos
Na página **4_Mapa_de_Grupos**.

## Observações
- Algumas filiais do seu arquivo já vieram pré-cadastradas.
- As capacidades da imagem foram incluídas para as filiais identificadas.
- Você pode editar tudo pela interface.
- O banco usado nesta versão é **SQLite local**, para ficar pronto e simples.
- Se depois quiser, eu adapto para **Supabase + deploy online**.
