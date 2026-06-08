# Plano de Desenvolvimento e Teste - Desafio Unicred

## 1. Compreensão e Requisitos (2-3 Dias)

*   **Objetivo:** Entender profundamente o escopo, os requisitos e as restrições do desafio.
*   **Atividades:**
    *   Análise Detalhada do `DesafioUnicred.md`
    *   Mapeamento de Casos de Uso:
        *   `Criar_Agenda()` - Adicionar uma nova pauta de votação.
        *   `Iniciar_Sessao_de_Votacao()` - Lançar uma sessão de votação.
        *   `Registrar_Voto()` - Receber votos (“Sim”/“Não”).
        *   `Calcular_Resultado()` - Determinar o resultado da votação.
    *   Definição de Requisitos Não Funcionais (RNFs):
        *   Escalabilidade:  Sustentação de centenas de milhares de votos.
        *   Persistência de Dados: Garantia de persistência dos votos.
        *   Versionamento da API: Estratégia clara para versionamento.
        *   Tratamento de Erros: Robustez no tratamento de erros e exceções.
*   **Entregas:** Documento de Requisitos Detalhado, Diagrama de Casos de Uso.

## 2. Desenvolvimento (7-10 Dias)

*   **Tecnologias:**
    *   **Linguagem:** Python
    *   **Framework:** FastAPI
    *   **Banco de Dados:** PostgreSQL
    *   **ORM:** SQLAlchemy
*   **Princípios de Design:**
    *   SOLID Principles (ênfase na manutenibilidade e legibilidade)
    *   Arquitetura Monolítica (adequada para o escopo)
*   **Práticas:**
    *   Versionamento com Git (Branching Strategy – ex: Gitflow)
    *   Gerenciamento de Dependências: Poetry ou pipenv
*   **Entregas:** Código Fonte (com documentação), Arquitetura do Projeto.

## 3. Testes (10-14 Dias)

*   **Pirâmide de Testes:**
    *   **Testes Unitários (Alto):** Componentes individuais – validação de dados, lógica de votação, etc.
    *   **Testes de Integração (Médio):** Interação entre componentes – API endpoints, banco de dados.
    *   **Testes de Sistema (Baixo):** Funcionamento da aplicação como um todo.
    *   **Testes de Aceitação (Baixo):** Verificação do cumprimento dos requisitos.
*   **Tipos de Testes:**
    *   Performance (Usando Locust)
    *   Segurança (Validação de entrada, prevenção de SQL Injection)
    *   Testes Automatizados (pytest, unittest)
*   **Gerenciamento de Dados de Teste:** Estratégia robusta para dados de teste (semeadura do banco de dados, geração de dados).
*   **Entregas:** Suite de Testes Automatizados, Relatório de Testes, Dados de Teste.

## 4. Tarefas Bônus de Teste (Conforme Necessário)

*   **Tarefa Bônus 1 (Integração com APIs Externas):** Mocking da API de usuário para simular respostas. Assertivas nos códigos de status HTTP.
*   **Tarefa Bônus 2 (Mensageria/Filas):** Testes para garantir o envio da mensagem de resultado da votação.
*   **Tarefa Bônus 3 (Performance):** Testes de carga com Locust para identificar gargalos.
*   **Tarefa Bônus 4 (Versionamento da API):** Testes de versionamento da API.

## 5. Documentação e Relatórios

*   **Documentação de Código:** Docstrings
*   **Documentação da API:** Swagger/OpenAPI
*   **Relatórios de Testes:** Métricas de cobertura, relatórios de bugs.
*   **Registro SDET:** Log detalhado das atividades de teste.

## Ferramentas

*   VS Code
*   Docker
*   Postman
*   Locust
*   pytest
*   Poetry/Pipenv

---

**Observações Importantes:**

*   Não iniciar o teste sem sanar todas as dúvidas.
*   Documentar claramente todas as dependências externas.
*   Testar exaustivamente a solução.
