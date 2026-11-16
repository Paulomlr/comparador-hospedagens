@echo off
rem 
cd /d "%~dp0"
start "Fornecedor A" cmd /k python fornecedores\fornecedor.py A 5001 0.5
start "Fornecedor B" cmd /k python fornecedores\fornecedor.py B 5002 1
start "Fornecedor C" cmd /k python fornecedores\fornecedor.py C 5003 1.5
start "Fornecedor D" cmd /k python fornecedores\fornecedor.py D 5004 2
