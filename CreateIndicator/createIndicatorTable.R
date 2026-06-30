MOEAs <- c("ARMOEA", "AdaW", "BiGE", "MOEAD", "MOEADD", "MOMBIII", "NSGAII", "RPEA", "SPEA2SDE", "SPEAR", "SRA", "Two_Arch2", "tDEA")
MOEAslbls <- c("ARMOEA", "AdaW", "BiGE", "MOEA/D", "MOEA/DD", "MOMBI-II", "NSGA-II", "RPEA", "SPEA2+SDE", "SPEAR", "SRA", "Two\\_Arch2", "tDEA")

#MOPs <- c("DTLZ1", "DTLZ2", "DTLZ5", "DTLZ7", "WFG1", "WFG2", "WFG3", "IDTLZ1", "IDTLZ2", "IWFG1", "IWFG2")
#DIMs <- c(2, 3, 4, 5, 6, 7, 8, 9, 10)

#MOPs <- c("IMOP1", "IMOP2", "IMOP3")
#DIMs <- c(2)

MOPs <- c("IMOP4", "IMOP5", "IMOP6", "IMOP7", "IMOP8", "VIE1", "VIE2", "VIE3")
DIMs <- c(3)


args = commandArgs(trailingOnly=TRUE)
if (length(args) != 6){
	stop("Arguments: extension MUST_MAXIMIZE dirInput dirOutput executeWilcoxon CARD")
}

extension = args[1]
MUST_MAXIMIZE = as.numeric(args[2])
dirInput = args[3]
dirOutput = args[4]
EXEC_WIlCOXON = as.numeric(args[5])
card = args[6]




outputFile = sprintf("%s/%s.tex", dirOutput, extension)
avgRnkFile = sprintf("%s/%s_avgRank.txt", dirOutput, extension)
cat("", file=avgRnkFile, sep="")





cat("\\begin{table}", file=outputFile, sep="\n")
cat("\\begin{tabular}{|c|c|", file=outputFile, sep="", append=TRUE)
for(i in 1:length(MOEAs)){
	cat("c|", file=outputFile, sep="", append=TRUE)
}
cat("}", file=outputFile, sep="\n", append=TRUE)
cat("\\hline", file=outputFile, sep="\n", append=TRUE)
cat("{\\bf MOP} & {\\bf N}", file=outputFile, sep=" ", append=TRUE)
for(i in 1:length(MOEAs)){
	line = sprintf("& {\\bf %s} ", MOEAslbls[i])
	cat(line, file=outputFile, sep=" ", append=TRUE)
}
cat("\\\\", file=outputFile, sep="\n", append=TRUE)
cat("\\hline", file=outputFile, sep="\n", append=TRUE)
############################ BEGINING OF AUTO-GENERATED TEXT ############################

for(mop in MOPs){
	line = sprintf("\\multirow{%d}{*}{%s}", length(DIMs), mop)
	cat(line, file=outputFile, sep="\n", append=TRUE)
	for(dim in DIMs){
		line = sprintf("& %d", dim)
		cat(line, file=outputFile, sep="\n", append=TRUE)

		VALUES = data.frame("MEAN" = 1:length(MOEAs), "STDDEV" = 1:length(MOEAs))
		SORT <- data.frame("ID" = 1:length(MOEAs), "MEAN" = 1:length(MOEAs))
		filter <- 1:length(MOEAs)
		for(i in 1:length(MOEAs)){
			filename = sprintf("%s/%s/%s/%s_%s_%.2dD.%s", dirInput, MOEAs[i], card, MOEAs[i], mop, dim, extension)

			if(file.exists(filename)){
				data = read.table(filename, header=FALSE)
				SORT[i, "ID"] = i
				SORT[i, "MEAN"] = mean(data$V1)

				VALUES[i, "MEAN"] = mean(data$V1)
				VALUES[i, "STDDEV"] = sd(data$V1)				
			
				filter[i] = 1
			}else{
				SORT[i, "ID"] = i;
				if(MUST_MAXIMIZE == 1){
					SORT[i, "MEAN"] = -Inf 
				}else{
					SORT[i, "MEAN"] = Inf 
				}
				filter[i] = 0
			}
		}
		if(MUST_MAXIMIZE){
			ordData = SORT[order(-SORT$MEAN),]
		}else{
			ordData = SORT[order(SORT$MEAN),]
		}

		WILCOX <- seq(0, length(MOEAs))
		if(EXEC_WIlCOXON == 1){
			moea_winner=ordData[1, "ID"];
			for(k in 1:length(MOEAs)){

				if(k != moea_winner){
					s1 = sprintf("%s/%s/%s/%s_%s_%.2dD.%s", dirInput, MOEAs[moea_winner], card, MOEAs[moea_winner], mop, dim, extension)
					s2 = sprintf("%s/%s/%s/%s_%s_%.2dD.%s", dirInput, MOEAs[k], card, MOEAs[k], mop, dim, extension)


					d1 = read.table(file=s1, header=FALSE)$V1
					d2 = read.table(file=s2, header=FALSE)$V1

					if(MUST_MAXIMIZE){
						W = wilcox.test(d1, d2, alternative="greater", conf.level=0.95, exact=FALSE)
					}else{
						W = wilcox.test(d1, d2, alternative="less", conf.level=0.95, exact=FALSE)
					}

					if(W$p.value <= 0.05){
						WILCOX[k] = 1
					}else{
						WILCOX[k] = 0
					}

				}else{
					WILCOX[k] = 2
				}
			}
		}
		

		for(k in 1:length(MOEAs)){
			if(filter[k] == 0){
				cat("& N/A", file=outputFile, sep="\n", append=TRUE)
				cat("N/A ", file=avgRnkFile, sep=" ", append=TRUE)
			}else{
				for(t in 1:length(MOEAs)){
					if(ordData[t, "ID"] == k){
						rank = t;
						break;
					}
				}

				if(rank == 1){
					line = sprintf("& \\cellcolor[gray]{0.5} \\specialcell{%.3e$^%d$ \\\\ (%.3e)}", VALUES[k, "MEAN"], rank, VALUES[k, "STDDEV"])
					cat(line, file=outputFile, sep="\n", append=TRUE)
				}else if(rank == 2){
					if(WILCOX[k] == 1){
						line = sprintf("& \\cellcolor[gray]{0.8} \\specialcell{%.3e$^%d$\\# \\\\ (%.3e)}", VALUES[k, "MEAN"], rank, VALUES[k, "STDDEV"])						
					}else{
						line = sprintf("& \\cellcolor[gray]{0.8} \\specialcell{%.3e$^%d$ \\\\ (%.3e)}", VALUES[k, "MEAN"], rank, VALUES[k, "STDDEV"])
					}
					cat(line, file=outputFile, sep="\n", append=TRUE)					
				}else{
					if(WILCOX[k] == 1){
						line = sprintf("& \\specialcell{%.3e$^%d$\\# \\\\ (%.3e)}", VALUES[k, "MEAN"], rank, VALUES[k, "STDDEV"])						
					}else{
						line = sprintf("& \\specialcell{%.3e$^%d$ \\\\ (%.3e)}", VALUES[k, "MEAN"], rank, VALUES[k, "STDDEV"])
					}
					cat(line, file=outputFile, sep="\n", append=TRUE)
				}

				line=sprintf("%d ", rank)
				cat(line, file=avgRnkFile, sep=" ", append=TRUE)
			}
		}
		cat("", file=avgRnkFile, sep="\n", append=TRUE)
		line = sprintf("\\\\ \\cline{2-%d}", length(MOEAs) + 2)
		cat(line, file=outputFile, sep="\n", append=TRUE)		
	}
	cat("\\hline", file=outputFile, sep="\n", append=TRUE)
	cat("\\hline", file=outputFile, sep="\n", append=TRUE)
}

############################## END OT AUTO-GENERATED TEXT ##############################
cat("\\hline", file=outputFile, sep="\n", append=TRUE)
cat("\\end{tabular}", file=outputFile, sep="\n", append=TRUE)
cat("\\end{table}", file=outputFile, sep="\n", append=TRUE)