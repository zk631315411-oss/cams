# Annotated bibliography for s6 explanation design

说明：这是 s6 解析生成研究的初筛书目，不是正式系统综述。下列文献的 DOI/题名已主要通过 Crossref 核验；本轮没有逐篇下载全文，因此具体机制性表述后续仍要回到全文确认。

## A. 反馈设计总论

1. Hattie, J., & Timperley, H. (2007). *The Power of Feedback*. Review of Educational Research. DOI: 10.3102/003465430298487
   - 相关性：把反馈拆成学习者需要回答的核心问题，例如目标是什么、当前在哪里、下一步怎么走。
   - 对 s6 的启发：解析不能只说“选 X”，应回答“这题考什么、为什么这个选项达标、下次怎么判”。
   - 使用边界：这是通用反馈框架，不直接告诉我们 CAMS 选择题解析应写多长。

2. Shute, V. J. (2008). *Focus on Formative Feedback*. Review of Educational Research. DOI: 10.3102/0034654307313795
   - 相关性：关注形成性反馈如何具体、及时、可执行，以及过度复杂反馈的风险。
   - 对 s6 的启发：解析应具体到题干信号和选项差异，但避免把教材全文堆给考生。
   - 使用边界：需要结合 CAMS 题型测试“多详细才不过载”。

3. Kluger, A. N., & DeNisi, A. (1996). *The effects of feedback interventions on performance*. Psychological Bulletin. DOI: 10.1037/0033-2909.119.2.254
   - 相关性：反馈并非天然有效，反馈方向、注意力焦点和任务相关性会影响效果。
   - 对 s6 的启发：解析应把注意力拉回题目判断任务，而不是泛泛评价考生能力。
   - 使用边界：它是反馈干预元分析，不是选择题解析专门研究。

4. Wisniewski, B., Zierer, K., & Hattie, J. (2020). *The Power of Feedback Revisited*. Frontiers in Psychology. DOI: 10.3389/fpsyg.2019.03087
   - 相关性：重新综合教育反馈研究，强调反馈效果与反馈层级、信息质量有关。
   - 对 s6 的启发：可以把解析分层：答案层、任务层、过程层、迁移层，而不是一段话混写。
   - 使用边界：Frontiers 开放期刊来源可用，但关键结论后续最好与 Hattie/Shute 等交叉核验。

5. Van der Kleij, F. M., Feskens, R. C. W., & Eggen, T. J. H. M. (2015). *Effects of Feedback in a Computer-Based Learning Environment on Students' Learning Outcomes*. Review of Educational Research. DOI: 10.3102/0034654314564881
   - 相关性：计算机学习环境中的反馈效果，和我们的自动解析系统接近。
   - 对 s6 的启发：系统生成解析时需要区分反馈类型，例如只给正确答案、给解释、给学习建议。
   - 使用边界：需进一步读全文确认不同反馈类型的效应差异。

6. Nicol, D. J., & Macfarlane-Dick, D. (2006). *Formative assessment and self-regulated learning*. Studies in Higher Education. DOI: 10.1080/03075070600572090
   - 相关性：强调反馈要支持学习者自我调节。
   - 对 s6 的启发：解析可以显式给出“自检问题”，例如“看到 best/initial/primary 时先判断什么”。
   - 使用边界：高等教育形成性评价框架，需转译为刷题场景。

## B. 测验与选择题反馈

7. Bangert-Drowns, R. L., Kulik, C.-L. C., Kulik, J. A., & Morgan, M. T. (1991). *The Instructional Effect of Feedback in Test-Like Events*. Review of Educational Research. DOI: 10.3102/00346543061002213
   - 相关性：直接讨论类测验事件中的反馈效果。
   - 对 s6 的启发：刷题后的反馈本身就是教学环节，解析应服务于纠错和再判断。
   - 使用边界：年代较早，后续应与更新的计算机反馈研究共同使用。

8. Kulik, J. A., & Kulik, C.-L. C. (1988). *Timing of Feedback and Verbal Learning*. Review of Educational Research. DOI: 10.3102/00346543058001079
   - 相关性：反馈时机与语言学习/测验反馈相关。
   - 对 s6 的启发：系统输出解析时要考虑“答题后立即反馈”的使用场景，解析应先给关键判断，再给展开依据。
   - 使用边界：不直接决定 s6 文本格式。

9. Butler, A. C., & Roediger, H. L. (2008). *Feedback enhances the positive effects and reduces the negative effects of multiple-choice testing*. Memory & Cognition. DOI: 10.3758/MC.36.3.604
   - 相关性：直接涉及 multiple-choice testing 和反馈，尤其是选择题可能强化错误干扰项的问题。
   - 对 s6 的启发：解析必须处理干扰项，不能只解释正确项；否则考生可能记住错误选项。
   - 使用边界：需读全文确认实验条件与 CAMS 题型的可迁移性。

10. Butler, A. C., Karpicke, J. D., & Roediger, H. L. (2008). *Correcting a metacognitive error*. Journal of Experimental Psychology: Learning, Memory, and Cognition. DOI: 10.1037/0278-7393.34.4.918
   - 相关性：反馈可以纠正低信心正确答案等元认知偏差。
   - 对 s6 的启发：解析不只服务错题，也服务“蒙对/低信心答对”的巩固；可考虑记录题目判断信心。
   - 使用边界：目前系统未采集考生信心，短期只能在解析中提示易混点。

11. Butler, A. C., Godbole, N., & Marsh, E. J. (2013). *Explanation feedback is better than correct answer feedback for promoting transfer of learning*. Journal of Educational Psychology. DOI: 10.1037/a0031026
   - 相关性：直接比较“只给正确答案”和“解释性反馈”对迁移的影响。
   - 对 s6 的启发：s6 不能退化成答案表；至少要有判断规则和类似题迁移提示。
   - 使用边界：需要全文确认“explanation feedback”的具体形式，避免误读为越长越好。

12. Mertens, U., & Lindner, M. A. (2025). *Computer-Based Answer-Until-Correct and Elaborated Feedback*. Journal of Computer Assisted Learning. DOI: 10.1111/jcal.13112
   - 相关性：较新的计算机化答题反馈研究，涉及 elaborate feedback 和 answer-until-correct。
   - 对 s6 的启发：后续可以测试“先让考生自纠/再看解析”的交互模式，但当前 md 解析先聚焦静态文本。
   - 使用边界：2025 新文献，需全文核验，且与单次输出 md 的使用方式不同。

13. Slepkov, A. D., & Godfrey, A. T. K. (2019). *Partial Credit in Answer-Until-Correct Multiple-Choice Tests Deployed in a Classroom Setting*. Applied Measurement in Education. DOI: 10.1080/08957347.2019.1577249
   - 相关性：选择题 answer-until-correct 与部分得分实践。
   - 对 s6 的启发：干扰项解析可按“为什么不够好/为什么只对一半”来写，尤其适合多选和最佳答案题。
   - 使用边界：评分机制研究多于解析文本研究。

## C. 检索练习、刷题与迁移

14. Roediger, H. L., & Karpicke, J. D. (2006). *Test-Enhanced Learning*. Psychological Science. DOI: 10.1111/j.1467-9280.2006.01693.x
   - 相关性：检索练习本身能促进保持。
   - 对 s6 的启发：解析后应强化“下次如何回忆/判断”，而不是只让考生重新阅读教材。
   - 使用边界：研究重点是测试效应，不是解析文案。

15. Roediger, H. L., & Karpicke, J. D. (2006). *The Power of Testing Memory*. Perspectives on Psychological Science. DOI: 10.1111/j.1745-6916.2006.00012.x
   - 相关性：把测试作为学习工具的理论和教育启示。
   - 对 s6 的启发：解析可以被设计为“刷题后的二次学习材料”。
   - 使用边界：需要结合 CAMS 的事实性/应用性题目差异。

16. Butler, A. C. (2010). *Repeated testing produces superior transfer of learning relative to repeated studying*. Journal of Experimental Psychology: Learning, Memory, and Cognition. DOI: 10.1037/a0019902
   - 相关性：重复测试对迁移的作用。
   - 对 s6 的启发：解析末尾的“类似题判断法”可能比纯教材复述更有价值。
   - 使用边界：需要后续用 CAMS 相似题验证迁移提示是否真有用。

17. Rowland, C. A. (2014). *The effect of testing versus restudy on retention*. Psychological Bulletin. DOI: 10.1037/a0037559
   - 相关性：测试效应元分析。
   - 对 s6 的启发：s6 可以服务于刷题闭环：作答 -> 判定 -> 解释 -> 再检索。
   - 使用边界：元分析层面，不直接给解析格式。

18. Adesope, O. O., Trevisan, D. A., & Sundararajan, N. (2017). *Rethinking the Use of Tests*. Review of Educational Research. DOI: 10.3102/0034654316689306
   - 相关性：实践测试的元分析。
   - 对 s6 的启发：解释系统应和题目练习系统联动，后续可以设计错题再练和同考点再练。
   - 使用边界：当前 s6 只研究解析文本，不负责练习调度。

19. Pan, S. C., & Rickard, T. C. (2018). *Transfer of test-enhanced learning*. Psychological Bulletin. DOI: 10.1037/bul0000151
   - 相关性：测试促进迁移的元分析。
   - 对 s6 的启发：解析要显式抽出可迁移判断规则，否则考生只会记住本题答案。
   - 使用边界：迁移效果受任务相似性影响，CAMS 需做题簇级验证。

20. Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., & Willingham, D. T. (2013). *Improving Students' Learning With Effective Learning Techniques*. Psychological Science in the Public Interest. DOI: 10.1177/1529100612453266
   - 相关性：有效学习技术综述，实践测试和分散练习通常证据较强。
   - 对 s6 的启发：解析可以配合复习策略，不应只提供一次性阅读文本。
   - 使用边界：不是选择题解析专文。

## D. 样例学习、自解释与解析结构

21. Chi, M. T. H., Bassok, M., Lewis, M. W., Reimann, P., & Glaser, R. (1989). *Self-Explanations*. Cognitive Science. DOI: 10.1207/s15516709cog1302_1
   - 相关性：学习者通过自解释理解样例解题过程。
   - 对 s6 的启发：解析应呈现“判断链”，让考生能复述为什么选/不选，而不是只看结论。
   - 使用边界：原研究多为问题解决学习，需转译为选择题。

22. Atkinson, R. K., Derry, S. J., Renkl, A., & Wortham, D. (2000). *Learning from Examples*. Review of Educational Research. DOI: 10.3102/00346543070002181
   - 相关性：样例学习原则综述。
   - 对 s6 的启发：高质量解析应像 worked example，展示从题干到选项排除的步骤。
   - 使用边界：不能把每道题都写成过长教程，需要按题目难度调节。

23. Renkl, A. (2002). *Worked-out examples: instructional explanations support learning by self-explanations*. Learning and Instruction. DOI: 10.1016/S0959-4752(01)00030-5
   - 相关性：说明 instructional explanations 如何支持自解释。
   - 对 s6 的启发：解析可以用“题干信号 -> 教材规则 -> 选项判定”的结构促进自解释。
   - 使用边界：需要测试对成熟考生是否嫌啰嗦。

## E. 认知负荷与解析长度

24. Sweller, J. (1988). *Cognitive Load During Problem Solving*. Cognitive Science. DOI: 10.1207/s15516709cog1202_4
   - 相关性：认知负荷理论基础之一。
   - 对 s6 的启发：解析应减少无关负荷，优先呈现本题判断所需信息。
   - 使用边界：基础理论文献，不是反馈实验。

25. Sweller, J., van Merrienboer, J. J. G., & Paas, F. G. W. C. (1998). *Cognitive Architecture and Instructional Design*. Educational Psychology Review. DOI: 10.1023/A:1022193728205
   - 相关性：工作记忆限制与教学设计。
   - 对 s6 的启发：可以把解析拆成“核心版”和“展开依据”，避免一次性塞满教材、KG 路径和所有边关系。
   - 使用边界：需要结合 markdown 输出和考生阅读习惯做实测。

26. Paas, F., Renkl, A., & Sweller, J. (2003). *Cognitive Load Theory and Instructional Design: Recent Developments*. Educational Psychologist. DOI: 10.1207/S15326985EP3801_1
   - 相关性：认知负荷理论在教学设计中的发展。
   - 对 s6 的启发：微缩教材可以作为第二层，而不是压进第一屏核心解析。
   - 使用边界：需要全文确认具体设计建议。
