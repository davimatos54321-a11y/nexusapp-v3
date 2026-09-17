name: Compile Kivy APK - Enterprise Grade v8

on:
  push:
    branches: [ main, master ]

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 40

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v4

    - name: Set up Python 3.10
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Clear and Isolate Cache v8
      uses: actions/cache@v4
      with:
        path: |
          .buildozer
          ~/.buildozer
        key: buildozer-cache-v8-${{ hashFiles('buildozer.spec') }}
        restore-keys: |
          buildozer-cache-v8-

    - name: Prepare Host Dependencies and 32-bit Architecture Support
      run: |
        sudo dpkg --add-architecture i386
        sudo apt-get update
        sudo apt-get install -y \
          git zip unzip openjdk-17-jdk python3-pip \
          autoconf libtool pkg-config zlib1g-dev \
          libncurses5-dev libncursesw5-dev cmake \
          libffi-dev libssl-dev patch \
          libc6:i386 libstdc++6:i386 libz1:i386

    - name: Manual Installation of Android NDK r23b and Complete SDK Toolchain
      run: |
        mkdir -p ~/.buildozer/android/platform
        cd ~/.buildozer/android/platform

        echo "--- Downloading Android NDK r23b ---"
        wget -q https://dl.google.com/android/repository/android-ndk-r23b-linux-x86_64.zip
        unzip -q android-ndk-r23b-linux-x86_64.zip
        rm android-ndk-r23b-linux-x86_64.zip

        echo "--- Downloading Android SDK Command-line Tools ---"
        mkdir -p android-sdk/cmdline-tools/latest
        wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip
        unzip -q commandlinetools-linux-9477386_latest.zip
        rm commandlinetools-linux-9477386_latest.zip
        
        mv cmdline-tools/* android-sdk/cmdline-tools/latest/
        rmdir cmdline-tools || true

        echo "--- Accepting Licenses and Installing Required Build-Tools & Platforms ---"
        export ANDROID_HOME="/home/runner/.buildozer/android/platform/android-sdk"
        export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
        
        # Aceita todas as licenças pendentes de forma forçada
        yes | sdkmanager --licenses || true
        
        # Instala os pacotes exigidos pelo Buildozer e API 33 / build-tools 37
        sdkmanager "platform-tools" "platforms;android-33" "build-tools;37.0.0" "build-tools;33.0.2"

    - name: Install Stable Toolchain Components
      run: |
        python3 -m pip install --upgrade pip
        python3 -m pip install "setuptools<66.0.0" "cython<3.0.0" "buildozer==1.5.0"

    - name: Execute Buildozer with Full Environment Ready
      env:
        IBM_API_KEY: ${{ secrets.IBM_API_KEY }}
      run: |
        buildozer -v android debug

    - name: Upload Verified APK Artifact
      uses: actions/upload-artifact@v4
      with:
        name: nexus-app-production-apk
        path: bin/*.apk
