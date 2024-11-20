from models import session, Foto, Obra, Diario

obra = session.query(Obra).filter_by(id=20).first()
session.delete(obra)
session.commit()