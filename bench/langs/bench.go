// bench.go - the programs of bench.4, in Go (bench/langs/run.py)
package main
import ("fmt"; "os")
func fib(n int) int { if n < 2 { return n }; return fib(n-1) + fib(n-2) }
func main() {
  r := 0
  switch os.Args[1] {
  case "fib": r = fib(32)
  case "loop": s := 0; for i := 0; i < 30000000; i++ { s += i }; r = s
  case "sieve": const N = 5000000; f := make([]bool, N); for i := range f { f[i] = true }
    for i := 2; i < N; i++ { if f[i] { r++; for j := i * i; j < N; j += i { f[j] = false } } }
  case "bubble": const NB = 3000; a := make([]int, NB); seed := 74755
    for i := range a { seed = (seed*1103515245 + 12345) & 2147483647; a[i] = seed % 1000000 }
    for i := 1; i < NB; i++ { for j := 0; j < NB-i; j++ { if a[j] > a[j+1] { a[j], a[j+1] = a[j+1], a[j] } } }
    for i, v := range a { r += v * (i + 1) }
  case "matrix": const NM = 150; var A, B [NM][NM]int
    for x := 0; x < NM; x++ { for y := 0; y < NM; y++ { A[x][y] = x + y; B[x][y] = y - x } }
    for x := 0; x < NM; x++ { for y := 0; y < NM; y++ { d := 0; for k := 0; k < NM; k++ { d += A[x][k] * B[k][y] }; r += d } }
  case "fannkuch": const n = 9; var p1, p, cnt [n]int; rr, maxf, pc, cs := n, 0, 0, 0
    for i := range p1 { p1[i] = i }
    loop: for { for rr != 1 { cnt[rr-1] = rr; rr-- }
      p = p1; f := 0
      for k := p[0]; k != 0; k = p[0] { for lo, hi := 0, k; lo < hi; lo, hi = lo+1, hi-1 { p[lo], p[hi] = p[hi], p[lo] }; f++ }
      if f > maxf { maxf = f }; if pc&1 == 1 { cs -= f } else { cs += f }
      for { if rr == n { r = cs*1000 + maxf; break loop }
        p0 := p1[0]; for i := 0; i < rr; i++ { p1[i] = p1[i+1] }; p1[rr] = p0
        cnt[rr]--; if cnt[rr] > 0 { break }; rr++ }
      pc++ }
  case "collatz": for i := 1; i < 100000; i++ { n, s := i, 0; for n > 1 { if n&1 == 1 { n = n*3 + 1 } else { n >>= 1 }; s++ }; r += s }
  }
  fmt.Println(r) }
