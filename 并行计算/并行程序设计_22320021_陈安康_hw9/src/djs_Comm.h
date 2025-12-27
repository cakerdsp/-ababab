// common.h
#ifndef COMMON_H
#define COMMON_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>

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

#endif
