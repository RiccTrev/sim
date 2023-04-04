from website import create_app  # posso farlo perché c'è __init__.py che rende la cartella un package

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
