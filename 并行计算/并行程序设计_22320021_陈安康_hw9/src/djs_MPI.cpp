#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <float.h>
#include <time.h>

#define INF DBL_MAX

typedef struct {
    int node;
    double weight;
} Edge;

typedef struct {
    Edge* edges;
    int edge_count;
    int edge_capacity;
} AdjList;

void add_edge(AdjList* graph, int u, int v, double w) {
    if (graph[u].edge_capacity == 0) {
        graph[u].edge_capacity = 4;
        graph[u].edges = (Edge*)malloc(sizeof(Edge) * 4);
    } else if (graph[u].edge_count == graph[u].edge_capacity) {
        graph[u].edge_capacity *= 2;
        graph[u].edges = (Edge*)realloc(graph[u].edges, sizeof(Edge) * graph[u].edge_capacity);
    }
    graph[u].edges[graph[u].edge_count++] = (Edge){v, w};
}

void read_graph(const char* filename, AdjList** graph, int* node_count) {
    FILE* fp = fopen(filename, "r");
    if (!fp) { perror("fopen graph"); exit(1); }

    char line[128];
    fgets(line, sizeof(line), fp);  // skip header
    int u, v;
    double w;
    int max_node = 0;

    int cap = 1024;
    *graph = (AdjList*)calloc(cap, sizeof(AdjList));

    while (fgets(line, sizeof(line), fp)) {
        sscanf(line, "%d,%d,%lf", &u, &v, &w);
        if (u >= cap || v >= cap) {
            int new_cap = (u > v ? u : v) + 128;
            *graph = (AdjList*)realloc(*graph, sizeof(AdjList) * new_cap);
            for (int i = cap; i < new_cap; ++i) {
                (*graph)[i].edges = NULL;
                (*graph)[i].edge_count = 0;
                (*graph)[i].edge_capacity = 0;
            }
            cap = new_cap;
        }
        add_edge(*graph, u, v, w);
        add_edge(*graph, v, u, w);
        if (u > max_node) max_node = u;
        if (v > max_node) max_node = v;
    }
    fclose(fp);
    *node_count = max_node + 1;
}

void read_test_pairs(const char* filename, int** pairs, int* pair_count) {
    FILE* fp = fopen(filename, "r");
    if (!fp) { perror("fopen test"); exit(1); }

    char line[128];
    fgets(line, sizeof(line), fp);  // skip header
    int u, v;
    int cap = 128, count = 0;
    *pairs = (int*)malloc(sizeof(int) * cap * 2);

    while (fgets(line, sizeof(line), fp)) {
        sscanf(line, "%d,%d", &u, &v);
        if (count >= cap) {
            cap *= 2;
            *pairs = (int*)realloc(*pairs, sizeof(int) * cap * 2);
        }
        (*pairs)[2 * count] = u;
        (*pairs)[2 * count + 1] = v;
        count++;
    }
    fclose(fp);
    *pair_count = count;
}

double dijkstra(AdjList* graph, int n, int src, int tgt) {
    double* dist = (double*)malloc(sizeof(double) * n);
    char* visited = (char*)calloc(n, sizeof(char));
    for (int i = 0; i < n; ++i) dist[i] = INF;
    dist[src] = 0;

    for (int i = 0; i < n; ++i) {
        int u = -1;
        double min_d = INF;
        for (int j = 0; j < n; ++j) {
            if (!visited[j] && dist[j] < min_d) {
                u = j;
                min_d = dist[j];
            }
        }
        if (u == -1 || u == tgt) break;
        visited[u] = 1;

        for (int j = 0; j < graph[u].edge_count; ++j) {
            int v = graph[u].edges[j].node;
            double w = graph[u].edges[j].weight;
            if (!visited[v] && dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
            }
        }
    }
    double result = dist[tgt];
    free(dist); free(visited);
    return result;
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    AdjList* graph = NULL;
    int* test_pairs = NULL;
    int node_count = 0, pair_count = 0;

    double start = MPI_Wtime();

    if (rank == 0) {
        read_graph("./updated_flower.csv", &graph, &node_count);
        read_test_pairs("./test_1000.csv", &test_pairs, &pair_count);
        printf("Graph loaded\n");
    }

    MPI_Bcast(&node_count, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&pair_count, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (rank != 0) {
        graph = (AdjList*)calloc(node_count, sizeof(AdjList));
    }

    for (int i = 0; i < node_count; ++i) {
        int edge_count = 0;
        if (rank == 0) edge_count = graph[i].edge_count;
        MPI_Bcast(&edge_count, 1, MPI_INT, 0, MPI_COMM_WORLD);
        graph[i].edge_count = edge_count;
        if (edge_count > 0) {
            if (rank != 0) {
                graph[i].edges = (Edge*)malloc(sizeof(Edge) * edge_count);
            }
            MPI_Bcast(graph[i].edges, sizeof(Edge) * edge_count, MPI_BYTE, 0, MPI_COMM_WORLD);
        }
    }

    if(rank == 0) printf("Graph broadcasted\n");

    if (rank != 0) {
        test_pairs = (int*)malloc(sizeof(int) * pair_count * 2);
    }
    MPI_Bcast(test_pairs, pair_count * 2, MPI_INT, 0, MPI_COMM_WORLD);

    if(rank == 0) printf("Test pairs broadcasted\n");

    double* local_results = (double*)malloc(sizeof(double) * pair_count);
    double* all_results = NULL;
    if (rank == 0) {
        all_results = (double*)malloc(sizeof(double) * pair_count);
    }

    for (int i = 0; i < pair_count; ++i) {
        if (i % size == rank) {
            int s = test_pairs[2 * i];
            int t = test_pairs[2 * i + 1];
            local_results[i] = dijkstra(graph, node_count, s, t);
        } else {
            local_results[i] = -1;
        }
    }

    MPI_Reduce(local_results, all_results, pair_count, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        printf("Results:\n");
        for (int i = 0; i < pair_count; ++i) {
            printf("Test case %d (%d -> %d): %.4f\n", i, test_pairs[2*i], test_pairs[2*i+1], all_results[i]);
        }
        printf("Task done\n");
        free(all_results);
    }
    free(local_results);
    
    double end = MPI_Wtime();
    if (rank == 0) printf("Total time: %.4f sec\n", end - start);

    MPI_Finalize();
    return 0;
}
