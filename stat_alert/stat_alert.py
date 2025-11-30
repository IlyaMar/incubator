from scipy.stats import beta

# Observed data
n = 10   # Total trials
k = 2    # Failures

# Prior: Beta(α₀=1, β₀=1)
alpha_prior, beta_prior = 1, 1

# Posterior parameters
alpha_post = alpha_prior + k
beta_post = beta_prior + (n - k)

# Posterior mean
mean_p = alpha_post / (alpha_post + beta_post)  # 0.25

# 95% credible interval
lower = beta.ppf(0.025, alpha_post, beta_post)  # ~0.07
upper = beta.ppf(0.975, alpha_post, beta_post)  # ~0.52

print("%f, %f" % (lower, upper))