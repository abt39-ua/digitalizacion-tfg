from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Ayuntamiento(Base):
    __tablename__ = "ayuntamientos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    nombre = Column(String, unique=True)
    password = Column(String)
    nivel_digitalizacion = Column(Float, nullable=True)

    # Campos principales sincronizados con Excel
    p1_formacion = Column(String, nullable=True)
    p2_competencias = Column(String, nullable=True)
    p3_infraestructuras = Column(String, nullable=True)

    # 🔗 Relación uno a uno con DatosAyuntamiento
    datos = relationship(
        "DatosAyuntamiento",
        back_populates="ayuntamiento",
        uselist=False,  # ⚙️ fuerza relación uno-a-uno
        cascade="all, delete-orphan"
    )


class DatosAyuntamiento(Base):
    __tablename__ = "datos_ayuntamiento"

    id = Column(Integer, primary_key=True, index=True)
    ayto_id = Column(Integer, ForeignKey("ayuntamientos.id"), unique=True)
    nivel_digitalizacion = Column(Float, nullable=True)
    data_json = Column(Text, nullable=True)  # JSON serializado con todas las columnas del Excel
    notas = Column(Text, nullable=True)

    # 🔗 Relación inversa con Ayuntamiento
    ayuntamiento = relationship("Ayuntamiento", back_populates="datos")
