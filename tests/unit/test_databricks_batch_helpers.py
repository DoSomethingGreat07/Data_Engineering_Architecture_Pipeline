import sys
import types


def install_pyspark_stub() -> None:
    pyspark = types.ModuleType("pyspark")
    sql = types.ModuleType("pyspark.sql")
    functions = types.ModuleType("pyspark.sql.functions")
    types_module = types.ModuleType("pyspark.sql.types")
    window_module = types.ModuleType("pyspark.sql.window")

    class FakeColumn:
        def __and__(self, other):  # noqa: ANN001
            return self

        def __invert__(self):
            return self

        def __ge__(self, other):  # noqa: ANN001
            return self

        def isin(self, values):  # noqa: ANN001
            return self

        def between(self, left, right):  # noqa: ANN001
            return self

        def isNotNull(self):  # noqa: N802
            return self

        def isNull(self):  # noqa: N802
            return self

        def desc(self):
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
    functions.when = lambda condition, value: FakeWhen()
    functions.row_number = lambda: types.SimpleNamespace(over=lambda window: FakeColumn())

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

    class Window:
        @staticmethod
        def partitionBy(*args, **kwargs):  # noqa: ANN002, ANN003, N802
            return types.SimpleNamespace(orderBy=lambda *order_args, **order_kwargs: object())

    sql.DataFrame = object
    sql.SparkSession = object
    types_module.StructType = StructType
    types_module.StructField = StructField
    types_module.StringType = StringType
    types_module.IntegerType = IntegerType
    types_module.TimestampType = TimestampType
    window_module.Window = Window

    sys.modules["pyspark"] = pyspark
    sys.modules["pyspark.sql"] = sql
    sys.modules["pyspark.sql.functions"] = functions
    sys.modules["pyspark.sql.types"] = types_module
    sys.modules["pyspark.sql.window"] = window_module


def test_pipeline_paths_generate_expected_locations() -> None:
    install_pyspark_stub()
    from databricks.batch.financial_batch_pipeline import PipelinePaths

    paths = PipelinePaths(
        bronze_root="s3://bucket/batch/raw",
        silver_root="s3://bucket/batch/silver",
        gold_root="s3://bucket/batch/gold",
        rejected_root="s3://bucket/batch/rejected",
    )

    assert paths.bronze_path("transactions") == "s3://bucket/batch/raw/transactions"
    assert paths.silver_path("transactions") == "s3://bucket/batch/silver/transactions"
    assert paths.gold_path("fact_transaction") == "s3://bucket/batch/gold/fact_transaction"
    assert paths.rejected_path("transactions") == "s3://bucket/batch/rejected/transactions"
