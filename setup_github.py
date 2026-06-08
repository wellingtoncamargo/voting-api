#!/usr/bin/env python3
"""
Script para criar o repositório 'voting-api' no GitHub e fazer o push inicial.

Pré-requisitos:
  1. Git instalado e configurado (git config --global user.email / user.name)
  2. GitHub CLI (gh) instalado — https://cli.github.com/
     OU um Personal Access Token em GH_TOKEN abaixo

Como usar:
  python setup_github.py
"""

import subprocess
import sys
import os

REPO_NAME = "voting-api"
GITHUB_USER = "wellingtoncamargo"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd: list[str], cwd: str = None, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or PROJECT_DIR, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"    {result.stdout.strip()}")
    if result.returncode != 0 and check:
        print(f"  ERRO: {result.stderr.strip()}")
        sys.exit(1)
    return result


def check_tool(name: str) -> bool:
    result = subprocess.run(["where" if sys.platform == "win32" else "which", name],
                            capture_output=True)
    return result.returncode == 0


def main():
    print("\n=== Unicred Voting API — Setup GitHub ===\n")

    # 1. Verificar ferramentas
    if not check_tool("git"):
        print("ERRO: Git não encontrado. Instale em https://git-scm.com/")
        sys.exit(1)

    has_gh = check_tool("gh")

    # 2. Inicializar repositório local
    print("[1/5] Inicializando repositório git...")
    run(["git", "init"])
    run(["git", "branch", "-M", "main"])

    # 3. Adicionar todos os arquivos
    print("\n[2/5] Adicionando arquivos...")
    run(["git", "add", "."])

    # 4. Commit inicial
    print("\n[3/5] Criando commit inicial...")
    run(["git", "commit", "-m",
         "feat: initial commit - Unicred Voting API\n\n"
         "- Clean Architecture (FastAPI + MongoDB + RabbitMQ)\n"
         "- CRUD completo para pautas, sessões, votos e associados\n"
         "- Validação de CPF matemática (módulo 11) + API externa opcional\n"
         "- Bônus 1-4 implementados (CPF, RabbitMQ, índices, versionamento)\n"
         "- 84 testes passando (unitários + API)\n"
         "- Docker Compose + CI/CD GitHub Actions"])

    # 5. Criar repositório no GitHub
    print(f"\n[4/5] Criando repositório '{REPO_NAME}' no GitHub...")
    if has_gh:
        result = run(
            ["gh", "repo", "create", REPO_NAME,
             "--public",
             "--description", "API REST de votação cooperativa — FastAPI + MongoDB + Clean Architecture",
             "--source", ".",
             "--remote", "origin",
             "--push"],
            check=False,
        )
        if result.returncode == 0:
            print(f"\n✓ Repositório criado e push realizado com sucesso!")
            print(f"  https://github.com/{GITHUB_USER}/{REPO_NAME}")
            return
        else:
            print("  gh falhou, tentando via HTTPS...")

    # Fallback: configurar remote manualmente
    print(f"\n[5/5] Configurando remote e fazendo push...")
    remote_url = f"https://github.com/{GITHUB_USER}/{REPO_NAME}.git"
    run(["git", "remote", "add", "origin", remote_url], check=False)
    run(["git", "remote", "set-url", "origin", remote_url], check=False)

    print(f"\n  ATENÇÃO: Crie o repositório manualmente em:")
    print(f"  https://github.com/new")
    print(f"  Nome: {REPO_NAME} | Visibilidade: Público | SEM inicializar com README")
    print(f"\n  Depois pressione ENTER para continuar com o push...")
    input()

    run(["git", "push", "-u", "origin", "main"])

    print(f"\n✓ Push realizado com sucesso!")
    print(f"  https://github.com/{GITHUB_USER}/{REPO_NAME}")


if __name__ == "__main__":
    main()
