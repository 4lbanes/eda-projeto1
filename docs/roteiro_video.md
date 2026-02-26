# Roteiro sugerido — Vídeo explicativo (até 10 minutos)

Requisito do enunciado: **máximo 10 min**, vídeo público (YouTube ou Drive), **mínimo 3 participantes** na narração.

## Estrutura (sugestão de tempo)

1. **Introdução (1:00)**  
   - Apresentar equipe e empresa analisada (Ibyte)  
   - Objetivos do projeto (o que queremos descobrir/diagnosticar)

2. **Tratamento de dados (2:00)**  
   - Abrir rapidamente o notebook `notebooks/01_limpeza_reclameaqui_ibyte.ipynb`  
   - Pontos principais: padronização, tipos, criação de `uf/estado`, `categoria_final`, `descricao_n_palavras` e `faixa_tamanho_texto`

3. **EDA (3:00)**  
   - Mostrar os principais achados do `notebooks/02_analise_exploratoria_reclameaqui_ibyte.ipynb`  
   - Exemplos: tendência + média móvel, sazonalidade, Pareto por UF, cruzamentos `STATUS × CATEGORIA/UF`, boxplot texto×status, WordCloud

4. **Dashboard (3:00)**  
   - Acessar o link do deploy e demonstrar os **filtros globais obrigatórios**: Estado, Status e Faixa do tamanho do texto  
   - Mostrar os componentes obrigatórios (série temporal, mapa por ano, Pareto, status, boxplot, WordCloud)

5. **Conclusão (1:00)**  
   - 3–5 recomendações de negócio baseadas nos achados  
   - Próximos passos (ex.: refinamento de categorias, monitoramento contínuo, melhorias operacionais)

## Dicas rápidas

- Grave em 1080p; evite rolagem rápida e zoom excessivo.
- Encerre o vídeo mostrando claramente o link do dashboard e reforçando os filtros obrigatórios.
