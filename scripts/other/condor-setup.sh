#!/bin/bash

echo "HOME = $HOME"
source $HOME/.bashrc
# echo "BLONDHOME = $BLONDHOME"
# cd $BLONDHOME

export CUDA_VISIBLE_DEVICES=0,1
export PYTHONPATH="./:$PYTHONPATH"

# echo "PATH = $PATH"
echo "PYTHONPATH = $PYTHONPATH"

gcc --version
mpirun --version
nvcc --version
nvidia-smi

INSTALL_DIR=$HOME/install

python blond/compile.py --with-fftw --with-fftw-threads --with-fftw-lib=$INSTALL_DIR/lib/ --with-fftw-header=$INSTALL_DIR/include/ -p --gpu

