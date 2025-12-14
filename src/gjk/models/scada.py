from sqlalchemy import Column, Integer, String

from gjk.models.message import Base


class ScadaSql(Base):
    """
    This is an ORM to track when a SCADA is officially
    live. Data before this point could be the system coming online,
    or even the scada in the lab.

    If start_s is None that means the SCADA is not yet live.

    This is a local hack, as eventually the GNodeId needs to be
    validated against the GNodeRegistry
    """

    __tablename__ = "scadas"
    g_node_id = Column(String, primary_key=True)
    g_node_alias = Column(String, nullable=False)
    short_alias = Column(String, nullable=False)
    scada_installed_s = Column(Integer)
    ta_fully_installed_s = Column(Integer)

    def to_dict(self):
        d = {
            "GNodeId": self.g_node_id,
            "GNodeAlias": self.g_node_alias,
            "ShortAlias": self.short_alias,
        }

        if self.scada_installed_s:
            d["ScadaInstalledS"] = self.scada_installed_s
        if self.ta_fully_installed_s:
            d["TaFullyInstalledS"] = self.ta_fully_installed_s

        return d

    def __repr__(self):
        return f"<ScadaSql({self.short_alias})>"

    def __str__(self):
        return f"<ScadaSql({self.short_alias})>"
