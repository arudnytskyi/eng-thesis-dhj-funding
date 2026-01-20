#import "pjatk-thesis-template.typ": thesis
#import "@preview/zebraw:0.6.1": *

#show: thesis.with(
  author: (
    name: "Arsen Rudnytskyi",
    id: "s28605"
  ),
  supervisor: (
    name: "dr hab. Andrzej Wodecki, prof. PJATK"
  ),
  
  thesis: (
    title-en: "Distilled Human Judgment for Public Goods Funding: Aligning LLM Voters to Human Juror Values",
    title-pl: "Distilled Human Judgment dla finansowania dóbr publicznych: \n dostosowanie opinii LLM do ocen ludzkich",
    type-en: "Engineering thesis",
    type-pl: "Praca inżynierska"
  ),

  abstracts: (
    en: [Allocating funding to public goods faces a fundamental trade-off: human jurors provide nuanced judgment regarding ecosystem value but cannot process thousands of repositories efficiently, while AI systems can operate at scale but often lack alignment with community values.

    The Distilled Human Judgment mechanism offers a solution by strategically leveraging human expertise on a sparse, representative sample of comparisons. This allows AI systems to provide comprehensive coverage, with final decisions optimally combining both inputs to ensure scalability without sacrificing human value grounding.],
    pl: [Alokowanie środków na dobra publiczne wiąże się z fundamentalnym kompromisem: ludzcy sędziowie dostarczają niuansowej oceny wartości dla ekosystemu, lecz nie są w stanie efektywnie przetwarzać tysięcy repozytoriów, podczas gdy systemy AI mogą działać na dużą skalę, ale często brakuje im zgodności z wartościami społeczności.

    Mechanizm Distilled Human Judgment oferuje rozwiązanie, polegające na strategicznym wykorzystaniu ludzkiej ekspertyzy na rzadkiej, reprezentatywnej próbie porównań. Dzięki temu systemy AI mogą zapewnić pełne pokrycie, a ostateczne decyzje w optymalny sposób łączą oba źródła, gwarantując skalowalność bez utraty zakorzenienia w ludzkich wartościach.],
    keywords-en: "Public goods funding, AI alignment, large language models (LLMs), human-in-the-loop (HITL)",
    keywords-pl: "Finansowanie dóbr publicznych, dopasowanie sztucznej inteligencji, duże modele językowe (LLM), człowiek w pętli decyzyjnej (HITL)",
  ),

  logos: (
    en: "images/PJAIT_en_poziom_1.svg",
    pl: "images/PJATK_pl_poziom_1.svg"
  ),

  bib-file: "bibliography.bib",
  source-code: "https://github.com/arudnytskyi/eng-thesis-dhj-funding"
)

= Introduction
== Background and Motivation
Allocating funding to public goods is a recurring governance problem in both traditional institutions and decentralized ecosystems. The task is judgment-intensive: decision-makers must balance technical importance, ecosystem externalities, long-term maintenance value, and the opportunity cost of scarce resources. In open-source funding settings, these difficulties are amplified by scale. A modern ecosystem can contain thousands of candidate repositories, while the pool of capable evaluators remains limited. This creates a persistent mismatch between the volume of decisions required and the amount of high-quality human attention available.

At the same time, contemporary AI voters (for example, large language models) can evaluate large collections of candidates quickly and consistently, making them attractive as scoring engines for large-scale ranking and prioritization. However, AI-only decision-making introduces a different failure mode: model outputs can be misaligned with the nuanced preferences and values that human jurors apply in governance contexts. As a result, purely AI-driven allocation risks optimizing for proxy signals rather than the judgment the allocation process is meant to reflect.

This thesis adopts a hybrid approach where AI voters provide scalable scoring while human jurors provide value grounding. The central challenge is not choosing between human judgment and AI scalability, but designing a mechanism that combines both in a principled and reproducible way.

== Problem Statement
Funding allocation for open-source infrastructure requires ranking candidates under severe information constraints. Human jurors can express nuanced preferences, detect context-specific importance, and apply ecosystem knowledge that is difficult to fully formalize. However, human review does not scale: even a relatively small task becomes expensive when it requires expert attention across many candidate repositories and many pairwise comparisons.

AI-only ranking scales well, but it introduces two risks. First, AI voter judgments can systematically diverge from human juror preferences, especially when the task depends on implicit norms (for example, how to weigh security, maintenance, and downstream dependency impact). Second, reliance on a single AI voter can create brittle failure modes and concentrated influence, where a single set of assumptions dominates outcomes.

The research problem addressed in this thesis is therefore:
+ How can a small budget of high-quality human comparisons be used to align an ensemble of AI voters to human juror judgment?
+ Can the resulting hybrid system support scalable funding allocation while maintaining acceptable agreement with human jurors?

This work focuses on a concrete dataset derived from a real funding-allocation setting: 47 unique repositories with 407 human-labeled pairwise comparisons (311 training comparisons and 96 held-out test comparisons). @cryptopond2025quantifying The labels express not only which repository is preferred, but also the magnitude of preference as a multiplicative ratio. This structure motivates operating in log-space, where multiplicative judgments become additive and can be modeled with standard regression objectives.

== Research Questions and Objectives
This thesis evaluates whether Distilled Human Judgment (DHJ) @buterin2025aihumans can enable scalable repository funding allocation while maintaining acceptable agreement with human evaluators. The evaluation is framed around three research questions.

Research questions:
+ DHJ mechanism quality: Given a fixed set of AI voters, how well does DHJ, as a mechanism that learns an optimal linear combination of voter scores, reproduce held-out human juror judgments on unseen comparisons?
+ Voter adequacy and representativeness: When instantiated with popular general-purpose LLMs as AI voters, how adequate are these voters at representing human juror values for this funding-ranking task, as evidenced by learned weight concentration, agreement metrics, and diagnostic error patterns (for example, multiplier distribution mismatch)?
+ Efficiency: How much human time is required to obtain a target level of agreement, as estimated from decision timestamps and comparison throughput?

To make these questions measurable, the primary outcome is directional agreement on pairwise comparisons. Two secondary outcomes capture magnitude and calibration: correlation with human log-ratios and Root Mean Squared Error (RMSE) in log-space.

Objectives:
- Implement an end-to-end DHJ pipeline that learns a non-negative, sum-to-one weighting over AI voter outputs from sparse human juror comparisons.
- Evaluate DHJ (as HITL) against an AI-only baseline on a held-out test set, using the human juror labels as the normative reference:
  - Human juror labels: define the targets for agreement and error metrics (normative reference, not a predictive baseline).
  - AI-only (single AI voter): a single model’s scoring output used directly as the decision rule. In this thesis, AI-only is defined as the voter that receives the smallest weight in the learned DHJ solution.
  - HITL (DHJ): the proposed mechanism where humans provide sparse supervision that shapes the aggregation rule over AI voters.
- Report agreement metrics (primary: directional accuracy; secondary: correlation and RMSE in log-space; plus diagnostic MSE and MAE) and analyze robustness under sparse, heavy-tailed human labels.
- Report efficiency using timestamps, including average time per comparison and implications for labeling budgets.

== Approach and Contributions
This thesis follows an implementation-first approach and then evaluates the resulting system against clearly defined baselines. DHJ is instantiated for repository funding allocation using two inputs: (i) sparse human juror comparisons that define the target preference signal, and (ii) multiple LLM-based AI voters that score the full repository set.

DHJ learns a convex, non-negative, sum-to-one weight vector over AI voters that best matches the human comparisons on a training split. The learned aggregation is then applied to score all repositories and produce a global ranking. Chapter 3 specifies the pipeline in full detail, including label encoding, voter prompting, and optimization.

The main contributions are:
+ A reproducible implementation of Distilled Human Judgment for repository funding allocation, including data preparation, model scoring, weight learning, and ranking output.
+ An empirical evaluation on a real-world dataset with 47 unique repositories and 407 human-labeled comparisons, using a held-out test set.
+ A comparison between DHJ (HITL) and an AI-only baseline using a primary directional accuracy metric and secondary calibration metrics (correlation and RMSE in log-space), complemented by efficiency analysis based on decision timestamps and robustness analysis under sparse, heavy-tailed multiplier labels. Human juror labels serve as the normative reference for all agreement and error metrics.

== Thesis Structure
This thesis is organized as follows. Chapter 2 reviews background on human AI collaboration, governance mechanisms for public goods funding, and how DHJ relates to ensemble alignment with preference data. Chapter 3 describes the implemented DHJ pipeline, including data encoding, AI voter scoring, and the constrained optimization used to learn aggregation weights. Chapter 4 presents the empirical evaluation, comparing AI-only and DHJ (as HITL) using agreement, calibration, and efficiency metrics, with human juror labels serving as the normative reference, and discussing robustness considerations arising from sparse and heavy-tailed human labels. Chapter 5 concludes with the main findings, limitations, and directions for future work.

= Related Work and Background
This chapter positions Distilled Human Judgment (DHJ) at the intersection of (i) human-AI collaboration and oversight, (ii) preference learning from pairwise comparisons, (iii) convex ensemble aggregation, and (iv) DAO governance and public goods funding mechanisms.

== Human-AI Collaboration and Oversight
=== Human-in-the-loop patterns and design guidance
Human-in-the-loop (HITL) is a broad design space where models support or partially automate decisions while humans retain oversight. HCI literature emphasizes that effective systems should communicate capabilities and limitations, allow appropriate correction, and avoid surprising users, especially in high-stakes settings. @amershi_guidelines_2019

In governance and funding allocation, the key difficulty is not only per-decision quality, but also global consistency across many comparisons. This motivates mechanisms where limited human input shapes a stable decision rule that then scales across the full candidate set.

=== Automation bias and overreliance risks
A common failure mode of AI-assisted decision making is automation bias: users may over-rely on system output and reduce vigilance, even when contradictory evidence exists. This risk is amplified when model outputs appear confident or “official”, and when institutional procedures treat automated output as authoritative. @Kahn2024AISafety

DHJ addresses this risk through two design choices. First, it does not rely on a single model; it allows multiple AI voters to compete. Second, human judgments are used as a supervision signal that determines which voters receive influence via learned weights, rather than letting any one voter anchor decisions by default.

== Learning from Human Preferences and Pairwise Comparisons
=== Foundational models for paired comparisons
Pairwise comparison data has a long history in psychometrics and statistics. Thurstone’s law of comparative judgment formalizes how comparative preferences can be mapped onto a latent scale. @thurstone1927 The Bradley-Terry family models outcomes of pairwise comparisons using positive latent scores, enabling inference of a global ranking from sparse comparisons. @bradley_terry_1952 Later surveys summarize how these models and extensions are used across domains and how they behave under sparsity and dependence. @cattelan2012

DHJ shares the same high-level goal as this line of work: recover a coherent latent score vector from sparse pairwise signals. The difference is that DHJ uses pairwise human judgments to learn an aggregation over external “voters” (LLM score vectors), rather than directly fitting a probabilistic comparison model to human labels.

=== Multiplicative judgments and multi-criteria decision analysis
Multi-criteria decision analysis (MCDA) frameworks often elicit human judgments as pairwise ratios, which is conceptually close to the multiplier labels used in this thesis. The Analytic Hierarchy Process (AHP) is a canonical example: it uses ratio-scale pairwise comparisons and derives priorities via an eigenvector method, together with a consistency notion. @saaty1977

In DHJ, multiplicative strength labels are encoded in log-space to obtain additive targets. This makes ratio judgments compatible with squared-error objectives and linear aggregation, while preserving both direction and strength information.

=== Preference-based learning and reward modeling
Modern machine learning has adopted pairwise preference labels as a scalable supervision signal. A widely cited example is preference-based reinforcement learning, where a reward model is learned from human comparisons and then used to optimize behavior. @christiano2017

DHJ is aligned with the same “distillation” idea: use a relatively small number of human comparisons to produce a scalable decision function. However, DHJ keeps the decision rule simple and auditable (a convex combination of voters), prioritizing interpretability and robustness over end-to-end model fine tuning.

== Ensemble Aggregation and Convex Weighting
DHJ learns a non-negative, sum-to-one weight vector over AI voters. This is closely related to ensemble learning approaches that combine multiple predictors via weighted aggregation. “Stacking” and the Super Learner framework formalize how to select an optimal weighted combination under a chosen loss function, often using cross-validation to avoid overfitting. @vanderlaan2007 Accessible overviews emphasize the conceptual similarity between stacking and a meta-learner that optimizes weights to improve predictive performance. @naimi2018

From an optimization perspective, DHJ is a convex ensemble: restricting weights to the simplex acts as regularization and keeps the combined model within the convex hull of the voters. Learning convex combinations has been studied both theoretically and empirically, including greedy and Frank-Wolfe style procedures. @nguyen2020

The key distinction is that DHJ’s objective is not generic predictive accuracy on features, but agreement with human pairwise judgments. The same convex weighting idea becomes a governance mechanism: weights represent influence among competing AI voters.

== DAOs, Governance, and Public Goods Funding
=== Token voting limitations and the need for alternatives
DAO governance often defaults to token voting, which can create plutocratic dynamics and low-participation equilibria. Buterin argues that governance designs should move beyond coin voting to reduce wealth-based dominance and better reflect legitimate stakeholder input. @buterin2021

Empirical studies also highlight persistent participation and concentration issues in DAO voting at scale, raising doubts about strong “one-token-one-vote” democratic interpretations. @liu2025

=== Futarchy and prediction-market governance
Futarchy proposes “vote on values, bet on beliefs”: humans set objectives, while prediction markets select policies expected to best achieve them. @hanson2007 This is relevant as a conceptual baseline for separating value specification from scalable aggregation.

DHJ differs in that it does not require a measurable welfare metric or liquid prediction markets. Instead, it uses direct human comparisons as the value signal and learns an aggregation over AI voters to scale that signal.

=== Quadratic funding and mechanism design for public goods
Quadratic funding (and related “liberal radicalism” mechanisms) is a prominent approach to funding public goods by amplifying broad-based support while limiting large-donor dominance. @buterin2018 While QF addresses an important incentive and aggregation problem, many ecosystems still face a practical bottleneck: evaluating which projects deserve support and in what magnitude.

DHJ targets this evaluation bottleneck by scaling the judgment process itself. It can be viewed as complementary to funding mechanisms like QF: DHJ produces a ranked or scored signal that can be used upstream of allocation rules.

== Positioning Distilled Human Judgment
Across these literatures, DHJ can be summarized as:
+ Preference distillation: sparse human pairwise judgments define the target signal. @christiano2017
+ Convex ensemble selection: a simple, interpretable aggregation rule is learned over many candidate voters. @vanderlaan2007 @nguyen2020
+ Governance application: the learned weights operationalize a separation between scalable computation (AI voters) and value grounding (human jurors), addressing known governance failure modes such as overreliance and concentrated influence. @Kahn2024AISafety @liu2025

The next chapter specifies the DHJ pipeline implemented in this thesis and explains how the learned weights are estimated from the Deep Funding comparison dataset.

= System Design and Implementation
== System Overview
The implemented system operationalizes Distilled Human Judgment as a two-layer decision pipeline. The first layer produces candidate scores from a set of AI voters, where each voter is an independent language model prompted to evaluate repository importance for a funding allocation setting. The second layer aggregates these scores using weights learned from a limited set of human juror comparisons, producing a single final score per repository.

Inputs:
- Repository set: 47 unique repositories to be ranked.
- Human juror comparisons: 407 pairwise judgments collected on a rolling basis, split into 311 training comparisons and 96 held-out test comparisons.
- AI voter outputs: per-repository scores from multiple popular LLMs, captured in a standardized format for downstream aggregation.

Processing steps:
+ Apply prompt-level calibration and validity checks on AI voter outputs (list length, 0–100 range, and the approximate-sum heuristic) to encourage comparability across voters.
+ Encode human judgments as log-ratios derived from multiplicative preference labels.
+ Convert AI voter score vectors to logits via a log transform and align them to the repository identifiers used in the human dataset.
+ Learn non-negative aggregation weights that sum to one by minimizing squared error between the aggregated AI logits and the human log-ratios on the training comparisons.
+ Produce the final repository ranking by applying the learned weights to all repositories and exponentiating back from log-space when needed for interpretation.

Outputs:
- A weight vector over AI voters that is interpretable as each voter’s contribution to the final decision function.
- Final repository scores and a global ranking.
- Evaluation artifacts computed on the held-out test set, including directional accuracy (primary), correlation and RMSE in log-space (secondary), and efficiency measures from timestamps.

== Data Collection and Label Encoding
=== Human judgment collection
Human supervision is provided as pairwise comparisons between repositories. For each comparison, a juror sees two repositories and answers two questions:
+ Direction: which repository is more important for the ecosystem.
+ Strength: by what multiplicative factor the preferred repository is more important (for example, 2×, 5×, 10×, 50×).

The jury was collected on a rolling basis during the Deep Funding competition. @deepfunding-jury Jurors entered through two pathways:
- Nomination tree: a juror completes a minimum batch of comparisons and nominates additional jurors.
- Expert invitations: additional jurors are invited based on expertise related to specific seed repositories and their dependencies.

In total, the dataset used in this thesis contains 37 jurors and 407 labeled comparisons. The split is constructed at the juror level: for each juror, 20% of that juror’s recorded comparisons are assigned to the test set and the remaining 80% to the training set, yielding 311 training comparisons and 96 held-out test comparisons overall. @pond2025quantifying

In addition to the judgment labels, the dataset includes timestamps for each decision. These timestamps are used in Chapter 4 to estimate average time per comparison and total human effort.

=== Repository universe and identifiers
The task is to rank repositories only. The repository universe contains 47 unique repositories. Each human label is a pairwise comparison that references a pair of repository identifiers (a, b) provided by human jurors.

AI voters do not provide pairwise labels. Instead, each AI voter outputs an absolute score vector on a 0 to 100 scale, rating every repository relative to its contribution to the parent repository’s success (as specified in the scoring prompt). All AI voter score vectors are aligned to the same identifier order as the human dataset so that, for any compared pair (a, b), the system can compute an implied preference signal from the AI scores (by comparing scores, and in log-space by taking differences of logits). This alignment ensures that human pairwise labels and AI absolute ratings refer to the same items without ambiguity.

#figure(
  box(inset: 0pt)[
    #image("images/ethereum_dependency_tree.svg")
  ],
  caption: [Example output ranking. Repository impact scores computed using Distilled Human Judgment. Hierarchical distribution across ecosystem categories]
)<dhj-output>

=== Encoding multiplicative labels in log-space
Human judgments are naturally multiplicative: $a$ juror may state that repository $b$ is $M$ times more important than repository $a$. DHJ represents these labels in log-space so that multiplicative ratios become additive targets.

For a comparison $k$ between repositories $(a_k, b_k)$ with multiplier $M_k > 0$, the target label is encoded as:
$ c_k = cases(
  ln(M_k) &"if" b_k "is preferred",
  -ln(M_k) &"if" a_k "is preferred"
) $

This encoding has two practical effects:
+ The sign captures directional preference.
+ The magnitude captures strength of preference on a scale that is compatible with linear aggregation.

=== Preprocessing assumptions
To ensure numerical stability, the pipeline enforces positivity of all scores before applying natural log (ln) transforms.

- Human multipliers are strictly positive by definition.
- AI voter scores are produced on a positive numeric scale. If a score of 0 can occur, it is clipped to a small epsilon before log transformation.

The resulting training set consists of $(a_k, b_k, c_k)$ tuples. This representation is used directly by the optimization module described in Section 3.4.

== AI Voters and Scoring
The implementation uses multiple large language models (LLMs) as AI voters. Each AI voter is asked to score the same fixed list of repositories, producing a numeric score per repository that can later be aggregated by DHJ.

Scoring is fully prompt-driven and produces a machine-readable output that is consumed by the aggregation code.

=== Scoring prompt and output format
For a given parent context (the target system whose success is being analyzed), each AI voter receives a prompt that:
- Specifies the evaluation criteria (historical impact, current ecosystem importance, security and decentralization, developer adoption, and technical influence).
- Lists the repositories to rate by name and URL.
- Requires the answer to be returned as a Python list of length 47 containing numbers on a 0 to 100 scale.
- Adds a soft calibration constraint: the scores should roughly sum to 47 × 50, encouraging comparable scale across voters.

The key design requirement is that the AI response is strictly structured. Any output that is not a valid list of 47 numeric values is treated as invalid and must be retried or discarded.

Code below shows the exact prompt template used to generate AI voter score vectors. The prompt defines the voter task framing, the scoring criteria, and the structured output contract consumed by the DHJ pipeline.

#figure(
  zebraw(
```python
def generate_scoring_prompt(repos: List[str], parent: str = "Ethereum") -> str:
  repo_names = [repo.split('/')[-1] for repo in repos]
  
  prompt = f"""You are evaluating open-source projects that contributed to {parent}'s success.
  
  Rate each project on a 0-100 scale based on:
  - Historical impact on {parent}'s development and adoption
  - Current importance to the ecosystem
  - Security, reliability, and decentralization contributions
  - Developer adoption and community usage
  - Technical innovation and influence on other projects
  
  Projects to rate:
  """
  
  for i, (repo_url, repo_name) in enumerate(zip(repos, repo_names), 1):
      prompt += f"{i}. {repo_name} ({repo_url})\n"
  
  prompt += f"""
  Provide your answer ONLY as a Python list of {len(repos)} numbers (0-100).
  The numbers should reflect relative importance and roughly sum to {len(repos) * 50}.
  
  Format: [score1, score2, score3, ...]
  No explanation. Just the list.
  """
  
  return prompt
```
  ),
  caption: [AI voter scoring prompt template],
  supplement: [Listing]
)

Note: the prompt-level sum heuristic is a soft calibration rule that encourages comparable scale across voters. It is not a hard constraint enforced by the optimization.

=== Score alignment and preprocessing
Each AI voter produces a score vector over the 47 repositories. These vectors are aligned to the repository identifier order used by the human comparison dataset.

To combine AI scores with human multiplicative labels, scores are transformed to logits. Because the log transform requires strictly positive inputs, any zero-valued outputs are clipped to a small epsilon before transformation.

The resulting per-voter logit vectors are used as inputs to the DHJ optimization described in Section 3.4.

=== AI voter roster
All models used as AI voters in the experiments are listed below.
- grok-3
- claude-sonnet-3.7
- claude-sonnet-4
- claude-sonnet-4.5
- claude-opus-4.1
- gemini-2.5-pro
- gemini-2.5-flash
- o3-mini
- o4-mini
- gpt-oss-120b
- gpt-5.1
- gpt-5-nano
- gpt-4.1
- llama-3.1-405b

== Optimization Formulation
DHJ learns a single aggregation rule that combines AI voter scores to best match human juror judgments. Following the implementation reference, log-transformed model scores are referred to as logits and all alignment is performed in log-space (natural logarithm)

#figure(
  table(
    columns: (auto, 1fr),
    inset: 10pt,
    align: (x, y) => if x == 0 { center } else { left },
    stroke: (x, y) => (
      top: if y == 0 or y == 1 { 1pt } else { 0pt },
      bottom: 1pt
    ),
    table.header(
      [*Symbol*], [*Description*]
    ),
    [$n$], [Total number of AI voters (models)],
    [$i$], [Index of an AI voter ($i = 1, dots, n$)],
    [$j$], [Index of a repository (candidate)],
    [$k$], [Index of a human comparison sample],
    [$w$], [Weight vector over AI voters ($w in RR^n$)],
    [$w^*$], [The optimal weights found by the solver],
    [$s_i^((j))$], [Raw score (positive) from voter $i$ for repo $j$],
    [$L_i^((j))$], [Logit from voter $i$ for repo $j$],
    [$tilde(L)^((j))$], [Ensemble combined logit for repo $j$],
    [$c_k$], [Human target value (log-difference) for comparison $k$],
    [$p_k(w)$], [Predicted difference for comparison $k$ given weights $w$],
    [$J(w)$], [Objective (Cost) function to be minimized],
    [$Delta^n$], [The unit simplex constraint set],
  ),
  caption: [Summary of mathematical notations used in the DHJ mechanism.],
  supplement: [Table],
) <tab-notations>

=== From scores to predicted comparisons
Each model $i$ outputs a positive score $s_i^((j))$ for every repository $j$. These scores are converted into logits:
$ L_i^((j)) = ln(s_i^((j))) $

#emph[Implementation-aligned computation] (as used in `find_optimal_weights()`, see @find-weights): Given a weight vector $w$ over AI voters, we first construct a single *combined logit vector* over repositories:
$ tilde(L)^((j))(w) = sum_(i=1)^n w_i L_i^((j)) $

Then, for each human-labeled comparison $k$ between repositories $(a_k, b_k)$, the ensemble prediction is computed as the difference on this combined vector:
$ p_k (w) = tilde(L)^((b_k)) (w) - tilde(L)^((a_k)) (w) $

=== Objective function
Human labels are encoded as signed log-multipliers $c_k$ (see Section 3.2.3). The DHJ mechanism seeks the optimal weights $w^*$ that minimize the squared disagreement between human targets and ensemble predictions.

We define the cost function $J(w)$ as:
$ J(w) = sum_k ( p_k (w) - c_k )^2 $

The optimal weights are obtained by minimizing this cost subject to simplex constraints:
$ w^* = arg min_(w in Delta^n) J(w) $

==== Matrix Formulation
To analyze the convexity of the problem, we can express the prediction $p_k(w)$ in matrix notation. Let $D in RR^(K times n)$ be the *comparison matrix*, where each entry represents the logit difference for model $i$ on comparison $k$:
$ D_{k,i} = L_i^((b_k)) - L_i^((a_k)) $

Let $c in RR^K$ be the vector of human targets. The ensemble prediction vector is simply $p(w) = D w$. The optimization problem then becomes a standard *Least Squares* problem on the simplex:

$ w^* = arg min_(w in Delta^n) ||D w - c||_2^2 $

where the feasible set is defined as:
$ Delta^n = { w in RR^n | w_i >= 0, forall i " and " sum_i w_i = 1 } $

Since the objective is a convex quadratic function (squared Euclidean norm) and the constraint set $Delta^n$ is a convex polytope, this optimization possesses a *unique global minimum*, which is efficiently solved by the SLSQP algorithm.

=== Constraints and solver
Weights are constrained to form a convex combination over voters:
- Non-negativity: $w_i >= 0, forall i$
- Normalization: $sum_(i=1)^n w_i = 1$

The implementation solves this constrained optimization using SciPy `minimize` with bound constraints for non-negativity and an equality constraint for the sum-to-one condition.

@find-weights shows the exact optimization core used to learn the DHJ weights. In the implementation, the ensemble first constructs a single combined logit vector from the weighted model logits lists, and then evaluates comparison error on that combined vector via `cost_function`. In this listing, `log` denotes the natural logarithm.

#figure(
  zebraw(
```python
def cost_function(logits, samples):
    # Calculate Squared Error between model differences and human targets
    return sum((logits[b] - logits[a] - c) ** 2 for a, b, c in samples)
    

def find_optimal_weights(logits_lists, samples):
    # Helper: Compute combined logits for a given weight vector
    def split_cost(weights):
        combined_logits = [
            sum(w * L[i] for w, L in zip(weights, logits_lists))
            for i in range(len(logits_lists[0]))
        ]
        return cost_function(combined_logits, samples)

    # Initial guess: equal weights
    initial_weights = [1 / len(logits_lists)] * len(logits_lists)

    # Constraint: weights must sum to 1
    constraints = ({'type': 'eq', 'fun': lambda w: sum(w) - 1})

    # Bounds: weights must be between 0 and 1
    bounds = [(0, 1)] * len(logits_lists)

    # Minimize the split cost
    result = minimize(
        split_cost,
        initial_weights,
        bounds=bounds,
        constraints=constraints
    )
    return result.x
```
  ),
  caption: [Weight learning via constrained least squares],
  supplement: [Listing]
)<find-weights>

Because the objective is convex quadratic and the feasible region is the probability simplex, the optimization has a well-defined global optimum and is numerically stable in practice.

=== Interpretation
The learned weight vector $w$ is directly interpretable: it specifies how much each AI voter contributes to the final decision function. Sparse solutions, where weight concentrates on a small subset of voters, indicate that only a few models closely track the human juror signal in this dataset.

=== Final Repository Scoring
Once the optimal weights $w^*$ are found, DHJ defines a final score $S_j$ for each repository $j$ by taking the weighted sum of logits and converting back to the multiplicative domain:

$ "score"^((j)) = exp( sum_(i=1)^n w_i^* L_i^((j)) ) $

This construction ensures that score ratios reflect the intended multiplicative structure in human judgments while preserving the interpretability of a model-weighted consensus.

== Reproducibility and Limitations
This prototype is designed to be reproducible at the level of data processing and aggregation, while acknowledging that LLM scoring can introduce variability.

=== Reproducibility controls
Data and splits:
- The repository universe is fixed at 47 repositories.
- The human dataset is split per juror, assigning 80% of each juror’s decisions to train and 20% to test. This split is computed once and stored as train.csv and test.csv.

Deterministic aggregation:
- Given fixed AI voter score vectors and a fixed train split, the DHJ weight learning step is deterministic up to numerical tolerance.
- The optimization uses a constrained solver with simplex constraints (sum-to-one and non-negativity). The objective is quadratic, which implies a unique global optimum in typical settings.

LLM scoring stability:
- AI voter score generation depends on the behavior of external models. To reduce parsing failures, the prompt enforces a strict output schema (a Python list of 47 numbers).
- All LLM API calls for scoring are executed with temperature set to 0 to reduce sampling variability and improve output determinism.
- Any non-conforming output is treated as invalid. In practice, this is handled via retry logic or by excluding the failed model output from that run.

=== Practical limitations
Dependence on voter set quality:
- DHJ is a mechanism that optimally combines available AI voter signals. If the voter set is systematically misaligned with human juror values, DHJ cannot fully recover the missing value signal.

Magnitude calibration limits:
- Human labels include extreme multipliers. Popular general-purpose models may compress score ranges and avoid extreme ratios, which can preserve directional accuracy while degrading magnitude metrics such as RMSE.

Juror heterogeneity and noise:
- The human labels are collected from multiple jurors with different expertise and priors. This can introduce inconsistency in both direction and magnitude judgments, placing a ceiling on achievable agreement.

System scope:
- The prototype is offline and does not include an interactive review loop during inference. Human input enters only through the training comparisons.

These limitations are revisited in Chapter 4 when interpreting results and in Chapter 5 when proposing future improvements (for example, more diverse voters, domain-tuned models, or alternative loss functions for heavy-tailed multipliers).

= Experimental Evaluation
== Dataset and Setup
The evaluation uses the same repository universe as the implementation.
- Unique repositories: 47.
- Human comparisons: 407 total, split into 311 training and 96 test comparisons.
- Jurors: 37.

The DHJ weights are learned using only the training comparisons (train.csv). Metrics are reported separately on the training split and on the held-out test split (test.csv). Test-set metrics are treated as the primary evaluation results, while training metrics are reported as a diagnostic for fit quality.

The task is evaluated in log-space using the encoded targets $c_k$. For each comparison $(a_k, b_k)$, the DHJ mechanism produces a predicted log-ratio $p_k (w^*)$, where $w^*$ is the weight vector learned on train.csv.

== Baseline Comparisons
The evaluation compares two predictive regimes against the same human comparison labels, which serve as the normative reference.

Normative reference (human jurors):
- The original human comparison labels define the targets $c_k$.
- Because these labels are the ground-truth reference used to compute agreement and error metrics, they are not treated as a predictive baseline with comparable metrics.

AI-only (single AI voter):
- Uses the output of a single AI voter as the final decision function.
- Direction is determined by comparing the voter scores for $a_k$ and $b_k$.
- Magnitude is taken as the voter’s implied log-ratio.
- In the main comparison, the chosen AI-only voter is the model that receives the smallest weight in the DHJ solution learned on the training split only (train.csv). In the reported run, the least-weighted voter is grok-3 with weight 0.0 (ties broken by the first occurrence in the model list). This provides a conservative baseline that reflects how a weak, poorly aligned single-model policy behaves on the task.

HITL (DHJ):
- Treats DHJ itself as the human-in-the-loop mechanism.
- Humans provide sparse supervision through labeled comparisons, and the system learns aggregation weights over AI voters to best match those judgments.
- Unlike interactive HITL systems, DHJ does not involve humans during inference; instead, human effort is concentrated in the training signal that shapes the aggregation rule.

Practical note:
- AI-only is intentionally instantiated as the least-weighted voter in the DHJ solution (weights learned on the training split only). This is a diagnostic baseline: it tests whether DHJ assigns low influence to a poorly aligned voter and whether the learned aggregation improves agreement relative to that weak single-voter policy.
- This baseline is not meant to estimate best-case single-model performance. Its purpose is to validate that the weight-learning mechanism discriminates between more and less aligned voters.

== Evaluation Metrics
The evaluation reports outcome metrics that capture both directional agreement and the calibration of preference magnitudes.

Primary metric: directional accuracy
- The fraction of comparisons where the model predicts the same winner as the human label (reported separately on train and test; test is primary).
- Computed by checking whether the sign of the prediction $p_k (w^*)$ matches the sign of the target $c_k$. A predicted value of 0 counts as agreement only when $c_k$ is exactly 0 (multiplier 1×); otherwise it is treated as disagreement.

Secondary metrics: correlation and RMSE in log-space
- Pearson correlation measures the linear dependence between predictions $p_k (w^*)$ and targets $c_k$. High correlation indicates that the model correctly ranks relative contributions, even if the absolute scale is shifted.
- RMSE measures the typical magnitude error in log-space; when exponentiated, it corresponds to an average multiplicative error factor.

Additional reported error metrics (diagnostic)
- MSE (log-space): mean squared error between $p_k (w^*)$ and $c_k$.
- MAE (log-space): mean absolute error between $p_k (w^*)$ and $c_k$. MAE is less sensitive to extreme multipliers than RMSE and is useful for separating direction errors from magnitude outliers.

Magnitude-aware diagnostics
- Agreement by multiplier magnitude: human multipliers are binned (log-spaced), and directional accuracy is reported per bin. This tests whether errors concentrate in extreme ratio ranges.
- Error by magnitude: mean absolute error is computed per multiplier bin to visualize how magnitude error scales with human ratio size.

In addition to outcome metrics, Chapter 4 reports efficiency metrics derived from decision timestamps.

== Results and Analysis
=== Main outcome metrics
The Results show that DHJ achieves strong directional agreement while only moderate magnitude alignment.
- Directional accuracy: 71.06% on training and 72.92% on test.
- Correlation: 0.4923 on training and 0.5481 on test.
- RMSE (log-space): 2.4800 on training and 2.3768 on test.
- MAE (log-space): 1.8497 on training and 1.7509 on test.

These results support the thesis framing of DHJ as a scalable HITL mechanism: sparse human supervision is sufficient to learn an aggregation rule that reproduces human directional preferences on unseen comparisons.

#figure(
  image("images/repository_rankings.svg"),
  caption: [Results of ranking (bar chart of top repositories by DHJ score). See example of an output @dhj-output]
)

@tab-results and @tab-summary-results are used in the next subsection to summarize the full metric comparison between DHJ (HITL) and AI-only (least-weighted voter) using the same train/test splits and metric definitions (with the test split treated as primary).

=== Diagnostic error metrics
To better understand magnitude error, Chapter 4 also reports MSE and MAE in log-space. MAE is particularly useful in this setting because it is less dominated by extreme multipliers than RMSE.

In addition, magnitude-aware diagnostics are used to localize failure modes:
- Directional accuracy is computed within multiplier bins to test whether mispredictions concentrate at specific ratio ranges.
- MAE is reported within the same bins to quantify how magnitude error scales with increasing human multiplier size.

These diagnostics are used to evaluate whether DHJ, when instantiated using only popular general-purpose LLM voters, primarily fails on extreme ratios even when it succeeds on direction.

#figure(
  image("images/agreement_rate_by_multiplier.svg"),
  caption: [Agreement rate between human and model sign judgments, binned by multiplier magnitude (comparing DHJ and AI‑only (least‑weighted: grok‑3).]
)

#figure(
  image("images/error_by_magnitude_ensemble.svg"),
  caption: [MAE vs multiplier magnitude (log‑spaced bins), comparing DHJ and AI‑only (least‑weighted: grok‑3).]
)

#figure(
  image("images/human_vs_ai_ensemble_multiplier_distribution.svg"),
  caption: [Distribution of human‑judged multipliers vs DHJ‑predicted multipliers on a log scale (train + test combined).]
)

#figure(
  image("images/human_vs_ai_least_multiplier_distribution.svg"),
  caption: [Distribution of human‑judged multipliers vs AI‑only (least‑weighted: grok‑3) predicted multipliers on a log scale (train + test combined).]
)

=== Weight sparsity and interpretation
The learned solution is sparse in practice: most weight concentrates on a small subset of AI voters, while the remaining voters receive weights near zero. This is consistent with the mechanism interpretation of DHJ: weights act as an empirical measure of which models best track the human juror signal in this dataset.

In the reported run, nearly all weight is assigned to three voters:
- claude-opus-4.1: 0.38889
- gpt-4.1: 0.32844
- llama-3.1-405b: 0.28267

All remaining voters receive weights close to zero.

=== Baseline comparison framing
The AI-only baseline is defined as the least-weighted voter in the DHJ solution (weights learned on the training split only). This is a diagnostic baseline that directly probes whether DHJ learns to assign low influence to misaligned voters.

Accordingly, improvements of DHJ over AI-only should be interpreted as evidence that the aggregation mechanism is doing useful selection: it down-weights poorly aligned voters and concentrates influence on voters whose score differences better match human comparisons.

=== Baseline results summary
This thesis reports a direct metric comparison between the DHJ ensemble and the AI-only baseline instantiated as the least-weighted voter.

- Directional accuracy is computed from sign agreement on predicted vs human log-ratios.
- Correlation, RMSE, and MAE are computed on the predicted and true log-ratio values over the same set of comparisons.

#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    inset: 10pt,
    align: (x, y) => if x < 2 { left } else { center },
    stroke: none, // Disable default grid lines for a cleaner look
    
    // --- Header ---
    table.hline(stroke: 1.5pt),
    table.header(
      [*Regime*], [*Split*], [*Dir. Acc.*], [*Corr. (ln)*], [*RMSE (ln)*], [*MAE (ln)*]
    ),
    table.hline(stroke: 0.7pt),

    // --- DHJ Rows ---
    [DHJ (HITL)], [Train], [71.06%], [0.4923], [2.4800], [1.8497],
    [DHJ (HITL)], [Test],  [72.92%], [0.5481], [2.3768], [1.7509],

    // --- Divider ---
    table.hline(stroke: 0.5pt + gray),

    // --- AI-Only Rows ---
    [AI-only \ (least-weighted)], [Train], [67.52%], [0.5217], [2.6407], [2.0515],
    [AI-only \ (least-weighted)], [Test],  [60.42%], [0.4704], [2.6101], [2.0173],
    
    // --- Footer Line ---
    table.hline(stroke: 1.5pt),
  ),
  caption: [Full metric comparison (train and test).],
  supplement: [Table],
) <tab-results>

Notes: metrics are computed in log-space using the same train/test splits. AI-only corresponds to the least-weighted voter selected by $"argmin"(w)$ on the learned weights (ties broken by first occurrence in the model list).

#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    inset: 10pt,
    align: (x, y) => if x == 0 { left } else { center },
    stroke: none,
    
    // --- Header ---
    table.hline(stroke: 1.5pt),
    table.header(
      [*Regime*], 
      [*Dir. Acc.* \ (primary)], 
      [*Corr.* \ (ln)], 
      [*RMSE* \ (ln)], 
      [*MAE* \ (ln)]
    ),
    table.hline(stroke: 0.7pt),

    // --- DHJ Row (Highlighted as Best) ---
    [DHJ (HITL)], 
    [*72.92%*], // Bolded because it's higher
    [*0.5481*], // Bolded because it's higher
    [*2.3768*], // Bolded because it's lower (better)
    [*1.7509*], // Bolded because it's lower (better)

    // --- AI-Only Row ---
    [AI-only \ (least-weighted)], 
    [60.42%], 
    [0.4704], 
    [2.6101], 
    [2.0173],
    
    // --- Footer ---
    table.hline(stroke: 1.5pt),
  ),
  caption: [Test-set summary metrics (primary and secondary).],
  supplement: [Table],
) <tab-summary-results>

Notes: directional accuracy is the primary metric. Correlation and error metrics are secondary and are reported in log-space.

== Efficiency Analysis
Efficiency is estimated from the decision timestamps included in the human comparison dataset. Rather than treating raw timestamp differences as ground truth “time spent” on a single comparison, the analysis approximates effort by measuring inter-decision gaps within each juror’s decision stream.

Method:
+ Parse timestamps as UTC datetimes and sort decisions by juror and time.
+ Compute per-juror inter-decision gaps using a group-wise difference.
+ Filter gaps to remove breaks and outliers:
  - Hard cutoff: discard gaps above a maximum threshold (default 30 minutes).
  - IQR filter: discard gaps outside the standard Tukey range $("Q1" − 1.5·"IQR", #v(1.5em) "Q3" + 1.5·"IQR")$.
+ Report summary statistics (min, max, mean, median, P75, P90) on the remaining gaps.

Latest run summary (current dataset):
- Total rows: 407; jurors: 37; missing timestamps: 0.
- Removed by max-gap cutoff (30 minutes): 46.
- Removed by IQR outlier filtering: 25.
- Inter-decision gaps used: 299.

Decision time statistics after filtering:
- Min: 7 seconds.
- Max: 12 minutes 44 seconds.
- Mean: 3 minutes 11 seconds.
- Median: 2 minutes 11 seconds.
- P75: 4 minutes 25 seconds.
- P90: 8 minutes 32 seconds.

#figure(
  image("images/decision_times.svg"),
  caption: [Distribution of filtered inter-decision gaps.]
)

The primary efficiency quantity used later in this thesis is the mean or median inter-decision gap, which can be multiplied by the number of labeled comparisons to estimate an approximate human time budget for a given training set size.

Approximate labeling budget examples:
- For the 311 training comparisons, the mean-based estimate is about 16.5 hours of active decision time (311 × 3 minutes 11 seconds). The median-based estimate is about 11.3 hours (311 × 2 minutes 11 seconds).
- For all 407 comparisons, the mean-based estimate is about 21.6 hours and the median-based estimate is about 14.8 hours.

These estimates should be interpreted as coarse approximations. They are based on filtered inter-decision gaps and may undercount effort when jurors read external context or work in interrupted sessions.

== Robustness: data sparsity and multiplier bias
Robustness is evaluated through properties of the available supervision signal and known failure modes of general-purpose LLM scoring on heavy-tailed ratio data. The emphasis is on what can be concluded from label sparsity, multiplier distributions, and diagnostic error patterns, rather than on additional ablation runs.

=== Sparse supervision relative to the item universe
The task contains 47 repositories, which implies 1,081 possible unordered pairs. Only 407 comparisons are labeled, and the labels are distributed across 37 jurors. As a result:

- Many repository pairs are never directly compared.
- The training objective relies on transitivity through the learned latent score vector rather than dense pairwise coverage.

This sparsity is a core motivation for DHJ, but it also limits how precisely any mechanism can recover fine-grained magnitude preferences.

=== Heavy-tailed multipliers and robustness of magnitude metrics
Human labels express multiplicative strength and can include extreme ratios. In log-space, extreme multipliers translate into large target magnitudes that dominate squared-error objectives. This makes RMSE highly sensitive to a small number of outlier comparisons.

For this reason, robustness is reported using both RMSE (secondary headline metric) and MAE (diagnostic), where MAE reduces the influence of a few extreme labels. Multiplier-binned accuracy and binned MAE further localize whether failures concentrate in the extreme tail.

=== Juror heterogeneity and potential bias
Jurors enter through different pathways (nomination tree and expert invitations) and may have different domain priors. Two forms of heterogeneity matter for robustness:

- Directional disagreement: different jurors may prefer different repositories in the same pair.
- Scale disagreement: even when direction matches, jurors may apply different multiplier magnitudes.

Both effects introduce label noise and can place a ceiling on achievable agreement for any model trained on pooled comparisons.

=== Why general-purpose LLMs struggle with extreme ratios
The scoring prompt requests 0 to 100 scores and encourages a roughly fixed total sum. This implicitly compresses the space of achievable ratios between repositories. As a result, a model can be directionally correct while still failing to match human magnitude labels, especially in cases where humans use very large multipliers.

This observation supports interpreting DHJ as a mechanism whose performance depends on the expressiveness of the available AI voters. If voters rarely represent extreme preference ratios, a convex combination cannot recover them.

=== Implications for mechanism design
The robustness observations in this chapter motivate two practical implications.

+ Metric choice matters: directional accuracy is relatively stable under sparse supervision, while magnitude metrics can be dominated by a small number of extreme multipliers. Reporting MAE alongside RMSE and using multiplier-binned diagnostics provides a more reliable picture of performance.
+ Voter expressiveness is a binding constraint: if most AI voters compress ratios due to prompt-level scoring constraints or model priors, a convex combination cannot reproduce extreme human multipliers. Improving magnitude fidelity therefore requires either more expressive voters or alternative scoring designs that allow a wider effective ratio range.

These implications are revisited in Chapter 5 as concrete directions for improving DHJ in funding allocation settings.

== Discussion
Two implementation-specific factors explain why RMSE can be high even when directional accuracy is strong.

+ Extreme multipliers in the human dataset: large ratios (for example, 50× to 999×) amplify squared error in log-space.
+ Compression in popular general-purpose LLMs: many models avoid extreme ratios and instead output mid-range values (for example, 20× to 50×), which limits how well any convex combination can match very large human ratios.

This motivates the thesis’s broader framing of DHJ as a mechanism: performance depends on the quality and diversity of the participating AI voters. As the voter set becomes more heterogeneous and more specialized, magnitude alignment is expected to improve without changing the DHJ optimization rule.

= Conclusion and Future Work
== Summary of Contributions
This thesis implemented and evaluated Distilled Human Judgment (DHJ) for repository funding allocation. The system combines multiple LLM-based AI voters with sparse human juror supervision expressed as pairwise comparisons with multiplicative strength. The implementation provides an end-to-end pipeline that:
- Collects and encodes human comparisons in log-space.
- Prompts AI voters to score a fixed repository set in a structured format.
- Learns a convex aggregation of AI voter scores by minimizing squared error against human log-ratio labels under simplex constraints.
- Produces a global ranking and evaluation artifacts on a held-out test set.

== Key Findings
The empirical evaluation supports three main findings.
+ DHJ reproduces human directional preferences with acceptable agreement under sparse supervision. Directional accuracy on the held-out test set exceeds 70%, indicating that the learned aggregation captures the sign of human preferences on unseen comparisons.
+ Magnitude alignment remains challenging in this setting. Correlation between predicted and human log-ratios is moderate, while RMSE in log-space remains high. This gap is consistent with heavy-tailed human multipliers and score compression effects in general-purpose LLM outputs.
+ The learned aggregation is interpretable and typically sparse. Weight concentration on a small subset of AI voters suggests that only a few models closely track the human juror signal in this dataset, and DHJ functions as a mechanism that amplifies aligned voters while down-weighting poorly aligned ones.

Mapping findings to research questions:
- RQ1 (DHJ mechanism quality) is addressed by the test-set agreement metrics in Chapter 4 and the learned weight solution that defines the aggregation rule.
- RQ2 (voter adequacy and representativeness) is addressed by weight concentration patterns and the diagnostic analyses that compare multiplier distributions and error as a function of multiplier magnitude.
- RQ3 (efficiency) is addressed by the timestamp-based decision-time analysis and labeling budget estimates in Section 4.5.

== Limitations
Several limitations constrain the conclusions.

Human label noise and heterogeneity:
- Juror expertise varies, and both directional and scale disagreement can occur across jurors.
- This creates an effective noise floor that can cap agreement.

Heavy-tailed multipliers:
- Extreme ratios dominate squared error losses in log-space, making RMSE sensitive to a small number of outliers.
- Reported diagnostic metrics (MAE and multiplier-binned analyses) are necessary to interpret performance beyond a single headline RMSE value.

Model dependence:
- DHJ cannot exceed the expressive limits of the available voter set. If all voters compress magnitude or share similar biases, a convex aggregation cannot fully reproduce extreme human ratios.

== Future Research Directions
The results suggest several concrete improvements.

+ Stronger and more diverse AI voters
  - Add domain-tuned models or tools that can reason about dependency graphs, security track records, and ecosystem usage.
  - Increase diversity to reduce correlated biases among voters.
+ Replication and external validity
  - Validate the pipeline on additional repository sets or additional rounds of funding decisions to test external validity.
  - Re-run the full evaluation multiple times under a fixed configuration to quantify run-to-run stability (for example, variability introduced by AI voter scoring and retry logic).
+ Tool-augmented AI voters via MCP
  - Overcome context bottlenecks: Mitigate the limits of prompt-only scoring by transitioning to agentic workflows that use the Model Context Protocol (MCP) @hou2025modelcontextprotocolmcp to access structured data.
  - Standardize evidence bundles: Require voters to query specific tools (for example, dependency graphs, maintenance activity, and ecosystem proxies) before scoring, grounding judgments in shared, verifiable signals rather than internal priors.
+ On-chain AI voter identities and auditable evaluation
  - Create immutable identities: Register AI voters in a smart contract registry that maps a persistent ID to a specific configuration (model name, prompt hash, and tool-suite hash) to ensure provenance.
  - Enable lightweight auditing: Publish compact run summaries on-chain including the learned weight vector $w^*$ and content hashes of score vectors, to make evaluations reproducible without requiring expensive on-chain inference.

Overall, the thesis supports DHJ as a practical mechanism for scaling repository funding allocation while keeping humans in control of values through sparse supervision. @buterin2025aihumans The remaining challenge is improving magnitude fidelity under heavy-tailed human labels, which motivates both better voters and more robust learning objectives.