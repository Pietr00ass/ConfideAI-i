class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password: str  # Dodajemy pole dla hasła
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    jobs: List["ScanJob"] = Relationship(back_populates="user")
