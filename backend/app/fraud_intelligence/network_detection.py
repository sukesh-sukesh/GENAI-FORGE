"""
InsureGuard AI - Network Detection Module
Graph-based fraud network detection (basic implementation).
Identifies clusters of related claims that may indicate organized fraud.
"""

from typing import Dict, Any, List, Set, Tuple
from sqlalchemy.orm import Session
from collections import defaultdict

from app.models.claim import Claim
from app.models.user import User


class FraudNetwork:
    """Simple graph-based fraud network detector."""

    def __init__(self):
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.node_types: Dict[str, str] = {}
        self.edge_details: List[Dict] = []

    def add_edge(self, node1: str, node2: str, edge_type: str):
        """Add a connection between two entities."""
        self.graph[node1].add(node2)
        self.graph[node2].add(node1)
        self.edge_details.append({
            "source": node1, "target": node2, "type": edge_type
        })

    def find_clusters(self, min_size: int = 3) -> List[Dict[str, Any]]:
        """Find connected components (potential fraud rings) in the graph."""
        visited = set()
        clusters = []

        for node in self.graph:
            if node not in visited:
                cluster = set()
                self._dfs(node, visited, cluster)
                if len(cluster) >= min_size:
                    clusters.append({
                        "nodes": list(cluster),
                        "size": len(cluster),
                        "risk_level": "critical" if len(cluster) > 5 else "high",
                        "node_types": {n: self.node_types.get(n, "unknown") for n in cluster}
                    })

        clusters.sort(key=lambda x: x["size"], reverse=True)
        return clusters

    def _dfs(self, node: str, visited: Set[str], cluster: Set[str]):
        """Depth-first search for connected components."""
        visited.add(node)
        cluster.add(node)
        for neighbor in self.graph[node]:
            if neighbor not in visited:
                self._dfs(neighbor, visited, cluster)


def detect_fraud_networks(db: Session) -> Dict[str, Any]:
    """
    Build a graph of related entities and detect potential fraud networks.
    Links: users → claims → repair_shops/hospitals → shared_attributes
    """
    network = FraudNetwork()

    # Get all claims with related data
    claims = db.query(Claim).all()

    for claim in claims:
        claim_node = f"claim_{claim.id}"
        user_node = f"user_{claim.user_id}"

        network.node_types[claim_node] = "claim"
        network.node_types[user_node] = "user"

        # User → Claim
        network.add_edge(user_node, claim_node, "filed_by")

        # Claim → Repair Shop
        if claim.repair_shop_name:
            shop_node = f"shop_{claim.repair_shop_name.lower().strip()}"
            network.node_types[shop_node] = "repair_shop"
            network.add_edge(claim_node, shop_node, "serviced_at")

        # Claim → Hospital
        if claim.hospital_name:
            hosp_node = f"hospital_{claim.hospital_name.lower().strip()}"
            network.node_types[hosp_node] = "hospital"
            network.add_edge(claim_node, hosp_node, "treated_at")

        # Claim → Location
        if claim.incident_location:
            loc_node = f"location_{claim.incident_location.lower().strip()}"
            network.node_types[loc_node] = "location"
            network.add_edge(claim_node, loc_node, "incident_at")

    # Find fraud clusters
    clusters = network.find_clusters(min_size=3)

    return {
        "total_nodes": len(network.graph),
        "total_edges": len(network.edge_details),
        "fraud_clusters": clusters,
        "total_clusters": len(clusters),
        "high_risk_clusters": len([c for c in clusters if c["risk_level"] == "critical"])
    }
