"""CLI runner for advanced quantitative model benchmarking."""

from services.benchmark_advanced import (
    AdvancedBenchmarkService,
    BENCHMARK_MODELS,
    BENCHMARK_QUESTIONS,
)


def main() -> None:
    benchmark = AdvancedBenchmarkService()

    df = benchmark.run(models=BENCHMARK_MODELS, questions=BENCHMARK_QUESTIONS)
    exported_files = benchmark.export_results(df)
    report_text = benchmark.generate_report(df)

    print("\n=== EXAMPLE RESULTS TABLE ===")
    print(df.head(10).to_string(index=False))

    print("\n=== MODEL AVERAGES ===")
    avg_df = (
        df.groupby("model", as_index=False)
        .agg(
            avg_response_time=("response_time", "mean"),
            avg_sql_validity=("sql_validity", "mean"),
            avg_consistency=("consistency_score", "mean"),
            avg_memory_mb=("memory_usage_mb", "mean"),
            avg_final_score=("final_score", "mean"),
        )
        .sort_values("avg_final_score", ascending=False)
    )
    print(avg_df.to_string(index=False))

    print("\n=== EXAMPLE REPORT TEXT ===")
    print(report_text)

    print("\n=== EXPORTED FILES ===")
    print(f"CSV: {exported_files['csv']}")
    print(f"Excel: {exported_files['excel']}")
    print(f"Report: {exported_files['report']}")


if __name__ == "__main__":
    main()
