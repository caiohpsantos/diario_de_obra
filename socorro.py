from models import session, Foto

for foto in session.query(Foto).filter_by(diario_id=36).all():
    print(foto.caminho_arquivo)
    session.delete(foto)
session.commit()