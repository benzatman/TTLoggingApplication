from app import create_app

# Create the Flask app instance
appp = create_app()

if __name__ == "__main__":
    appp.run(debug=True)
