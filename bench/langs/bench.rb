# bench.rb - the programs of bench.4, in Ruby (bench/langs/run.py)
def fib(n) = n < 2 ? n : fib(n - 1) + fib(n - 2)
r = case ARGV[0]
when 'fib' then fib(32)
when 'loop' then s = 0; i = 0; while i < 30000000; s += i; i += 1; end; s
when 'sieve' then n = 5000000; f = Array.new(n, true); c = 0; i = 2
  while i < n; if f[i]; c += 1; j = i * i; while j < n; f[j] = false; j += i; end; end; i += 1; end; c
when 'bubble' then nb = 3000; seed = 74755; a = Array.new(nb) { seed = (seed * 1103515245 + 12345) & 2147483647; seed % 1000000 }
  i = 1; while i < nb; j = 0; while j < nb - i; (a[j], a[j + 1] = a[j + 1], a[j]) if a[j] > a[j + 1]; j += 1; end; i += 1; end
  s = 0; a.each_with_index { |v, k| s += v * (k + 1) }; s
when 'matrix' then nm = 150; a = Array.new(nm) { |x| Array.new(nm) { |y| x + y } }; b = Array.new(nm) { |x| Array.new(nm) { |y| y - x } }
  s = 0; x = 0; while x < nm; y = 0; while y < nm; d = 0; k = 0; while k < nm; d += a[x][k] * b[k][y]; k += 1; end; s += d; y += 1; end; x += 1; end; s
when 'fannkuch' then n = 9; p1 = (0...n).to_a; cnt = Array.new(n, 0); rr = n; maxf = 0; cs = 0; pc = 0; res = nil
  loop do
    while rr != 1; cnt[rr - 1] = rr; rr -= 1; end
    p = p1.dup; f = 0
    while (k = p[0]) != 0; lo = 0; hi = k; while lo < hi; p[lo], p[hi] = p[hi], p[lo]; lo += 1; hi -= 1; end; f += 1; end
    maxf = f if f > maxf; cs += pc.odd? ? -f : f
    brk = false
    loop do
      if rr == n then res = cs * 1000 + maxf; brk = true; break end
      p0 = p1[0]; i = 0; while i < rr; p1[i] = p1[i + 1]; i += 1; end; p1[rr] = p0
      cnt[rr] -= 1; break if cnt[rr] > 0; rr += 1
    end
    break if brk
    pc += 1
  end; res
when 'collatz' then t = 0; i = 1; while i < 100000; n = i; s = 0; while n > 1; n = n.odd? ? n * 3 + 1 : n >> 1; s += 1; end; t += s; i += 1; end; t
end
puts r
