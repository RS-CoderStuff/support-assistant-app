class MetadataFilterBuilder:
    def build(self, metadata: dict[str, str]) -> dict:
        filters = [{"equals": {"key": key, "value": value}} for key, value in metadata.items() if key in {"product", "component", "environment", "source_type"}]
        if not filters:
            return {}
        return filters[0] if len(filters) == 1 else {"andAll": filters}
