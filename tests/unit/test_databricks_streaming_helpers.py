import sys
import types


def install_pyspark_streaming_stub() -> None:
    pyspark = types.ModuleType("pyspark")
    sql = types.ModuleType("pyspark.sql")
    functions = types.ModuleType("pyspark.sql.functions")
    types_module = types.ModuleType("pyspark.sql.types")

    class FakeColumn:
        def __and__(self, other):  # noqa: ANN001
            return self

        def __or__(self, other):  # noqa: ANN001
            return self

        def __invert__(self):
            return self

        def __eq__(self, other):  # noqa: ANN001
            return self

        def __lt__(self, other):  # noqa: ANN001
            return self

        def isin(self, values):  # noqa: ANN001
            return self

        def between(self, left, right):  # noqa: ANN001
            return self

        def isNotNull(self):  # noqa: N802
            return self

        def isNull(self):  # noqa: N802
            return self

        def cast(self, kind):  # noqa: ANN001
            return self

        def alias(self, name):  # noqa: ANN001
            return self

    class FakeWhen:
        def when(self, condition, value):  # noqa: ANN001
            return self

        def otherwise(self, value):  # noqa: ANN001
            return FakeColumn()

    functions.col = lambda name: FakeColumn()
    functions.lit = lambda value: FakeColumn()
    functions.current_timestamp = lambda: FakeColumn()
    functions.to_date = lambda value: FakeColumn()
    functions.to_json = lambda value: FakeColumn()
    functions.struct = lambda *values: FakeColumn()
    functions.from_json = lambda value, schema: FakeColumn()
    functions.when = lambda condition, value: FakeWhen()

    class StructType(list):
        pass

    class StructField:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            self.args = args
            self.kwargs = kwargs

    class StringType:
        pass

    class IntegerType:
        pass

    class TimestampType:
        pass

    class BooleanType:
        pass

    sql.DataFrame = object
    sql.SparkSession = object
    types_module.StructType = StructType
    types_module.StructField = StructField
    types_module.StringType = StringType
    types_module.IntegerType = IntegerType
    types_module.TimestampType = TimestampType
    types_module.BooleanType = BooleanType

    sys.modules["pyspark"] = pyspark
    sys.modules["pyspark.sql"] = sql
    sys.modules["pyspark.sql.functions"] = functions
    sys.modules["pyspark.sql.types"] = types_module


def test_streaming_paths_generate_expected_locations() -> None:
    install_pyspark_streaming_stub()
    from databricks.streaming.financial_streaming_pipeline import StreamingPaths

    paths = StreamingPaths(
        silver_root="s3://bucket/streaming/silver",
        gold_root="s3://bucket/streaming/gold",
        rejected_root="s3://bucket/streaming/rejected",
        checkpoint_root="s3://bucket/streaming/checkpoints",
    )

    assert paths.silver_path("transactions") == "s3://bucket/streaming/silver/transactions"
    assert paths.gold_path("fact_transaction") == "s3://bucket/streaming/gold/fact_transaction"
    assert paths.rejected_path("events") == "s3://bucket/streaming/rejected/events"
    assert paths.checkpoint_path("events") == "s3://bucket/streaming/checkpoints/events"

