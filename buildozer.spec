name: Compile Kivy APK

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Cache Buildozer global directory
        uses: actions/cache@v4
        with:
          path: |
            .buildozer
            bin/
          key: ${{ runner.os }}-buildozer-${{ hashFiles('buildozer.spec') }}-${{ hashFiles('*.py') }}
          restore-keys: |
            ${{ runner.os }}-buildozer-

      - name: Install System Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            git zip unzip openjdk-17-jdk python3-pip autoconf libtool \
            pkg-config zlib1g-dev libncurses5-dev ncurses-dev libssl-dev \
            libffi-dev libsqlite3-dev libbz2-dev

      - name: Install Buildozer and Dependencies
        run: |
          pip install --upgrade pip
          pip install --upgrade cython==0.29.36 buildozer pcpp

      - name: Run Buildozer Clean & Compilation
        run: |
          # Garante que o ambiente está totalmente limpo de resquícios antigos
          buildozer clean
          # Executa o build em modo verboso para depuração precisa
          buildozer -v android debug

      - name: Upload APK Artifact
        uses: actions/upload-artifact@v4
        with:
          name: package
          path: bin/*.apk
