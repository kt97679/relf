# &&/|| chains whose left-hand piece recurses back into the same
# splitter. The chain's remainder and pending operator are held across
# that call, so they must be per-invocation.
{ true && echo inner; } && echo outer
{ echo a && echo b; } && echo c && echo d
{ false || echo r; } && echo s
true && echo p && echo q
false || echo t || echo u
{ true; } && { true && echo nested; } && echo last
