// Exhaustive DSATUR. First-use color renaming is the only symmetry reduction.
// Output UNSAT means this search completed; it is not a DRAT certificate.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <set>
#include <string>
#include <vector>

struct Search {
    int n, k;
    std::vector<std::vector<int>> adj, count;
    std::vector<int> color, degree;
    std::vector<std::uint32_t> mask;
    std::uint64_t nodes = 0;
    bool aborted = false;
    double seconds;
    std::chrono::steady_clock::time_point start = std::chrono::steady_clock::now();
    bool dfs(int remaining, int used) {
        if (!remaining) return true;
        ++nodes;
        if ((nodes & 8191) == 0 && std::chrono::duration<double>(
                std::chrono::steady_clock::now()-start).count() > seconds) {
            aborted = true; return false;
        }
        int v=-1, best=-1, best_degree=-1;
        for (int i=0; i<n; ++i) if (color[i]<0) {
            int saturation=__builtin_popcount(mask[i]);
            if (saturation==k) return false;
            if (saturation>best || (saturation==best && degree[i]>best_degree)) {
                v=i; best=saturation; best_degree=degree[i];
            }
        }
        std::uint32_t options=((std::uint32_t(1)<<std::min(k,used+1))-1)&~mask[v];
        while (options) {
            std::uint32_t bit=options&-options; options-=bit;
            int c=__builtin_ctz(bit); color[v]=c;
            for (int u:adj[v]) if (color[u]<0) {
                if (count[u][c]++==0) mask[u]|=bit;
                --degree[u];
            }
            if (dfs(remaining-1,std::max(used,c+1))) return true;
            for (int u:adj[v]) if (color[u]<0) {
                if (--count[u][c]==0) mask[u]&=~bit;
                ++degree[u];
            }
            color[v]=-1;
            if (aborted) return false;
        }
        return false;
    }
};

int main(int argc,char**argv) {
    if (argc<3 || argc>4) { std::cerr<<"usage: color graph.txt k [seconds=60]\n"; return 2; }
    Search s;
    try { s.k=std::stoi(argv[2]); s.seconds=argc==4?std::stod(argv[3]):60; }
    catch (...) { std::cerr<<"Invalid numeric argument\n"; return 2; }
    int m;
    std::ifstream in(argv[1]);
    if (s.k<1 || s.k>30 || !(s.seconds>0) || !(in>>s.n>>m) || s.n<1 || m<0 ||
            m>1LL*s.n*(s.n-1)/2) { std::cerr<<"Invalid input\n"; return 2; }
    s.adj.resize(s.n);
    std::set<std::pair<int,int>> seen;
    for(int i=0,u,v;i<m;++i) {
        if (!(in>>u>>v) || u<0 || v<0 || u>=s.n || v>=s.n || u==v ||
                !seen.insert(std::minmax(u,v)).second) { std::cerr<<"Invalid edge\n"; return 2; }
        s.adj[u].push_back(v); s.adj[v].push_back(u);
    }
    std::string trailing;
    if (in>>trailing) { std::cerr<<"Extra graph data\n"; return 2; }
    s.color.assign(s.n,-1); s.mask.assign(s.n,0); s.degree.resize(s.n);
    s.count.assign(s.n,std::vector<int>(s.k,0));
    for (int i=0;i<s.n;++i) s.degree[i]=s.adj[i].size();
    bool sat=s.dfs(s.n,0);
    std::cout<<(sat?"SAT":s.aborted?"UNKNOWN":"UNSAT")<<" n="<<s.n<<" nodes="<<s.nodes
             <<" time="<<std::chrono::duration<double>(std::chrono::steady_clock::now()-s.start).count()<<"\n";
    if (sat) { for(int c:s.color) std::cout<<c<<' '; std::cout<<'\n'; }
    return sat?10:s.aborted?0:20;
}
