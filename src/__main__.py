import sys
import os

# Добавляем путь к родительскому каталогу
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == '__main__':
    from main import main
    main() 