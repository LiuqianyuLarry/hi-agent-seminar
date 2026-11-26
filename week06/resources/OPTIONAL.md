# After the report

Finish the four core functions first. Choose one experiment from the course menu. Tell the mentor what difference you expect. Each run writes its own lesson_result.json.

* **bench** runs all labelled questions with keyword search, vector search and fusion. Open retrieval_results.csv. Pick one section and compare its rank with and without metadata filtering.
* **semantic** needs sentence-transformers and a local sentence model directory in W6_MODEL_PATH. The lecture illustrates a 384-dimensional encoder. The runner measures the dimension of your model. Set W6_RERANKER_PATH only if you also have a local cross-encoder. Check the encoder and reranker names in the saved trace.
* **postgres** needs a dedicated classroom PostgreSQL database with pgvector, psycopg, the local encoder and a matching Week 6 index. The index builder is pg_setup.py. On a fresh dedicated database, create a local seed with `python seed.py --db work/engineering.sqlite`, then consult `python pg_setup.py --help` for the encoder, model and database arguments. Use W6_ADMIN_DATABASE_URL only during setup. The student runner takes its read-only connection from DATABASE_URL and verifies the corpus and encoder before searching.
* **deepseek** uses one API request and sends the classroom packet. Review its contents and approve the call first. Configure DEEPSEEK_API_KEY and DEEPSEEK_MODEL privately in your environment. Use the live requirements in a separate environment. The runner saves the returned wording and checks that cited IDs occur in the packet. Read the cited lines before signing off.

The core uses Python's standard library. These optional dependencies are needed only for the comparison you choose.

