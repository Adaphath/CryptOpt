/**
 * Copyright 2023 University of Adelaide
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { execSync } from "child_process";
import { appendFileSync, existsSync, rmSync } from "fs";
import { Measuresuite } from "measuresuite";
import { tmpdir } from "os";
import { join, resolve as pathResolve } from "path";

import ChartJsImage from 'chartjs-to-image';

import { assemble } from "@/assembler";
import { FiatBridge } from "@/bridge/fiat-bridge";
import { CHOICE, FUNCTIONS } from "@/enums";
import { errorOut, ERRORS } from "@/errors";
import {
  analyseMeasureResult,
  generateResultFilename,
  LOG_EVERY,
  padSeed,
  PRINT_EVERY,
  shouldProof,
  toggleFUNCTIONS,
  writeString,
} from "@/helper";
import globals from "@/helper/globals";
import Logger from "@/helper/Logger.class";
import { Model } from "@/model";
import { Paul, sha1Hash } from "@/paul";
import { RegisterAllocator } from "@/registerAllocator";
import { AnalyseResult, OptimizerArgs } from "@/types";

import { genStatistics, genStatusLine, logMutation, printStartInfo } from "./optimizer.helper";
import { init } from "./optimizer.helper.class";

let choice: CHOICE;

export class Optimizer {
  private measuresuite: Measuresuite;
  private libcheckfunctionDirectory: string; // aka. /tmp/CryptOpt.cache/yolo123
  private symbolname: string;
  public getSymbolname(deleteCache = false): string {
    if (deleteCache) {
      this.cleanLibcheckfunctions();
    }
    return this.symbolname;
  }

  public constructor(private args: OptimizerArgs) {
    Paul.seed = args.seed;

    const randomString = sha1Hash(Math.ceil(Date.now() * Math.random())).toString(36);
    this.libcheckfunctionDirectory = join(tmpdir(), "CryptOpt.cache", randomString);

    const { measuresuite, symbolname } = init(this.libcheckfunctionDirectory, args);

    this.measuresuite = measuresuite;
    this.symbolname = symbolname;

    globals.convergence = [];
    globals.mutationLog = [
      "evaluation,choice,kept,PdetailsBackForwardChosenstepsWaled,DdetailsKindNumhotNumall",
    ];
    // load a saved state if necessary
    if (args.readState) {
      Model.import(args.readState);
    }
    RegisterAllocator.options = args;
  }

  private no_of_instructions = -1;
  private asmStrings: { [k in FUNCTIONS]: string } = {
    [FUNCTIONS.F_A]: "",
    [FUNCTIONS.F_B]: "",
  };
  private numMut: { [id: string]: number } = {
    permutation: 0,
    decision: 0,
  };
  private numRevert: { [id: string]: number } = {
    permutation: 0,
    decision: 0,
  };

  private revertFunction = (): void => {
    /**intentionally blank */
  };
  /** you usually don't want to mess with @param random.
   * mutate should not be called from outside with @param random=false*/
  private mutate(random = true): void {
    if (random) {
      choice = Paul.pick([CHOICE.PERMUTE, CHOICE.DECISION]);
    }
    Logger.log("Mutationalita");
    switch (choice) {
      case CHOICE.PERMUTE: {
        Model.mutatePermutation();
        this.revertFunction = () => {
          this.numRevert.permutation++;
          Model.revertLastMutation();
        };
        this.numMut.permutation++;
        break;
      }
      case CHOICE.DECISION: {
        const hasHappend = Model.mutateDecision();
        if (!hasHappend) {
          // this is the case, if there is no hot decisions.
          choice = CHOICE.PERMUTE;
          this.mutate(false);
          return;
        }
        this.revertFunction = () => {
          this.numRevert.decision++;
          Model.revertLastMutation();
        };

        this.numMut.decision++;
      }
    }
  }

  public optimise() {
    return new Promise<number>((resolve) => {
      Logger.log("starting optimisation");
      printStartInfo({
        ...this.args,
        symbolname: this.symbolname,
        counter: this.measuresuite.timer,
      });
      let batchSize = 200;
      const numBatches = 31;
      let ratioString = "";
      let numEvals = 0;

      Logger.dev(`Opt Config: ${this.args.optimizerConfig?.option}`);

      // measurements
      // collect all improvements to calculate the average, median and stddeviation
      const improvements: number[] = [];

      // collect all worse solutions accepted to calculate the average, median and stddeviation
      const worsenings: number[] = [];

      // balanced initial temperature = -(AVERAGE_DELTA/(ln(ACCEPTANCE_RATE)))
      const k = 1;
      const averageDelta = 190;
      let acceptanceRate = 0.85;
      if (this.args.optimizerConfig?.option === "SA") {
        acceptanceRate = this.args.optimizerConfig.acceptanceRate;
      }

      const initialTemperature = Math.abs((k * averageDelta) / Math.log(acceptanceRate));
      Logger.dev(`initial temperature: ${initialTemperature}`);
      let temperature = initialTemperature;

      // geometric cooling scheme
      // constant alpha for temperature cooling scheme
      let alpha = 0.95;
      if (this.args.optimizerConfig?.option === "SA") {
        alpha = this.args.optimizerConfig.coolingRateAlpha ?? alpha;
      }

      // statistics for worse solutions accepted
      let countWorseSolutions = 0;
      let countWorseSolutionsAccepted = 0;
      let nextEvaluationCheckpoint = Math.ceil(0.01 * this.args.evals);
      let worseSolutionStatistics: number[] = [];
      let currentRatioStatistics: {
        x: number;
        y: number;
      }[] = [];
      
      // temperature length
      // fixed number of evaluations
      let temperatureLengthType: string = "TL1";
      if (this.args.optimizerConfig?.option === "SA") {
        temperatureLengthType = this.args.optimizerConfig.temperatureLengthType ?? temperatureLengthType;
      }
      let lengthConstant = 50 / 10000;
      if (this.args.optimizerConfig?.option === "SA" && this.args.optimizerConfig.temperatureLengthType === "TL1") {
        lengthConstant = this.args.optimizerConfig.lengthConstant ?? lengthConstant;
      }
      const temperatureLengthEvals = Math.ceil(lengthConstant * this.args.evals);

      // adaptive temperature length (TL6) -> reduce temperature when a certain threshold of accepted solutions is reached
      let threshholdOfAcceptedSolutions = 100;
      if (this.args.optimizerConfig?.option === "SA" && this.args.optimizerConfig.temperatureLengthType === "TL6") {
        threshholdOfAcceptedSolutions = this.args.optimizerConfig.threshholdOfAcceptedSolutions ?? threshholdOfAcceptedSolutions;
      }
      let numberOfAcceptedSolutions = 0;

      // adaptive temperature length (TL7) -> reduce temperature if the last x solutions were worse
      let checkLastIterations = 5;
      if (this.args.optimizerConfig?.option === "SA" && this.args.optimizerConfig.temperatureLengthType === "TL7") {
        checkLastIterations = this.args.optimizerConfig.checkLastIterations ?? checkLastIterations;
      }
      let improvementsInLastIterations: boolean[] = [];


      Logger.dev(`temperature length: ${temperatureLengthEvals}`);

      const optimistaionStartDate = Date.now();
      let accumulatedTimeSpentByMeasuring = 0;
      

      let currentNameOfTheFunctionThatHasTheMutation = FUNCTIONS.F_A;
      let time = Date.now();
      const startTime = new Date();
      let show_per_second = "many/s";
      let per_second_counter = 0;
      const intervalHandle = setInterval(() => {
        if (numEvals > 0) {
          // not first eval, thus we want to mutate.
          this.mutate();
        }

        Logger.log("assembling");
        const { code, stacklength } = assemble(this.args.resultDir);

        Logger.log("now we have the current string in the object, filtering");
        const filteredInstructions = code.filter((line) => line && !line.startsWith(";") && line !== "\n");
        this.no_of_instructions = filteredInstructions.length;

        // and depening on the silent-opt use filtered or the verbose ones for the string
        if (this.args.verbose) {
          const c = code.join("\n");
          writeString(pathResolve(this.libcheckfunctionDirectory, "current.asm"), c);
          this.asmStrings[currentNameOfTheFunctionThatHasTheMutation] = c;
        } else {
          this.asmStrings[currentNameOfTheFunctionThatHasTheMutation] = filteredInstructions.join("\n");
        }

        // check if this was the first round
        if (numEvals == 0) {

          // then point to fB and continue, write first
          if (this.asmStrings[FUNCTIONS.F_A].includes("undefined")) {
            const p = pathResolve(this.libcheckfunctionDirectory, "with_undefined.asm");
            writeString(p, this.asmStrings[FUNCTIONS.F_A]);


            const e = `\n\n\nNah... we dont want undefined; wrote ${p}, plx fix. \n\n\n`;
            console.error(e);
            throw new Error(e);
          }
          currentNameOfTheFunctionThatHasTheMutation = FUNCTIONS.F_B;
          numEvals++;
        } else {
          //else, it was not the first round, we need to measure

          const now_measure = Date.now();

          let analyseResult: AnalyseResult | undefined;
          try {
            Logger.log("let the measurements begin!");
            if (this.args.verbose) {
              writeString(
                pathResolve(this.libcheckfunctionDirectory, "currentA.asm"),
                this.asmStrings[FUNCTIONS.F_A],
              );
              writeString(
                pathResolve(this.libcheckfunctionDirectory, "currentB.asm"),
                this.asmStrings[FUNCTIONS.F_B],
              );
            }
            // here we need the barriers
            const results = this.measuresuite.measure(batchSize, numBatches, [
              this.asmStrings[FUNCTIONS.F_A],
              this.asmStrings[FUNCTIONS.F_B],
            ]);
            Logger.log("well done guys. The results are in!");

            accumulatedTimeSpentByMeasuring += Date.now() - now_measure;

            analyseResult = analyseMeasureResult(results, { batchSize, resultDir: this.args.resultDir });

            //TODO increase numBatches, if the times have a big stddeviation
            //TODO change batchSize if the avg number is batchSize *= avg(times)/goal ; goal=10000 cycles
          } catch (e) {
            const isIncorrect = e instanceof Error && e.message.includes("tested_incorrect");
            const isInvalid = e instanceof Error && e.message.includes("could not be assembled");
            if (isInvalid || isIncorrect) {
              writeString(
                join(this.args.resultDir, "tested_incorrect_A.asm"),
                this.asmStrings[FUNCTIONS.F_A],
              );
              writeString(
                join(this.args.resultDir, "tested_incorrect_B.asm"),
                this.asmStrings[FUNCTIONS.F_B],
              );
              writeString(
                join(this.args.resultDir, "tested_incorrect.json"),
                JSON.stringify({
                  nodes: Model.nodesInTopologicalOrder,
                }),
              );
            }

            if (isIncorrect) {
              errorOut(ERRORS.measureIncorrect);
            }
            if (isInvalid) {
              errorOut(ERRORS.measureInvalid);
            }
            writeString(join(this.args.resultDir, "generic_error_A.asm"), this.asmStrings[FUNCTIONS.F_A]);
            writeString(join(this.args.resultDir, "generic_error_B.asm"), this.asmStrings[FUNCTIONS.F_B]);
            errorOut(ERRORS.measureGeneric);
          }

          const [meanrawA, meanrawB, meanrawCheck] = analyseResult.rawMedian;

          batchSize = Math.ceil((Number(this.args.cyclegoal) / meanrawCheck) * batchSize);
          // We want to limit for some corner cases.
          batchSize = Math.min(batchSize, 10000);
          batchSize = Math.max(batchSize, 5);

          const currentFunctionIsA = () => currentNameOfTheFunctionThatHasTheMutation === FUNCTIONS.F_A;

          Logger.log(currentFunctionIsA() ? "New".padEnd(10) : "New".padStart(10));

          let kept: boolean;
          
          // first calculate the absolute improvement between the mutated and the function before
          const absoluteImprovement = currentFunctionIsA() ? meanrawA - meanrawB : meanrawB - meanrawA;


          // Compare the two functions
          // Local random search: if the new function is better, keep it.
          // Simulated Annealing: Acceptance Criterion -> Metropolis condition

          // local random search compares meanRawA and meanRawB
          const mutatedIsBetter = (meanrawA <= meanrawB && currentFunctionIsA()) || (meanrawA >= meanrawB && !currentFunctionIsA());


          if (!mutatedIsBetter)
            countWorseSolutions++;

          // adaptive temperature length -> reduce temperature if the last x solutions were worse
          improvementsInLastIterations.push(mutatedIsBetter);

          // collect the improvements and worsenings
          if (mutatedIsBetter)
            improvements.push(absoluteImprovement);
          else 
            worsenings.push(absoluteImprovement);

          // metroplis condition for simulated annealing
          // use the relative improvement
          const metropolisCondition = Math.exp((-absoluteImprovement) / temperature);

          const metropolis = mutatedIsBetter || metropolisCondition > Math.random();
          
          if (
            (this.args.optimizer === "LS"  && mutatedIsBetter) || // local random search
            (this.args.optimizer === "SA" && metropolis) // simulated annealing
          ) {
            // worse function is kept because of metropolis condition
            if (this.args.optimizer === "SA" && metropolis && !mutatedIsBetter) {
              // Logger.dev(`Kept worse function. Metropolis condition: ${metropolisCondition}`);
              // Logger.dev(`absolute improvement: ${absoluteImprovement}`);
              // Logger.dev(`Current temperature: ${temperature}`);

              // increase the number of worse solutions accepted
              countWorseSolutionsAccepted++;
            }
            kept = true;
            currentNameOfTheFunctionThatHasTheMutation = toggleFUNCTIONS(
              currentNameOfTheFunctionThatHasTheMutation,
            );
          } else {
            // revert
            kept = false;
            this.revertFunction();
          }

          // Simulated Annealing: Temperature Updates (temperature length, temperature restart, cooling scheme)
          if (this.args.optimizer === "SA") {
            Logger.log(`temperature: ${temperature}`);
            // Temperature Length
            // fixed number of evaluations
            if (temperatureLengthType === 'TL1' && numEvals % temperatureLengthEvals === 0) {
              // Decrease temperature
              temperature = temperature * alpha;
              
              Logger.dev(`New temperature: ${temperature}`);
            }

            // adaptive temperature length (TL6)
            if (temperatureLengthType === 'TL6' && kept) {
              // increase the number of accepted solutions
              numberOfAcceptedSolutions++;
            }
            if (temperatureLengthType === 'TL6' && numberOfAcceptedSolutions >= threshholdOfAcceptedSolutions) {
              // Decrease temperature
              temperature = temperature * alpha;
              
              Logger.dev(`New temperature: ${temperature}`);

              // reset the number of accepted solutions
              numberOfAcceptedSolutions = 0;
            }

            if (temperatureLengthType === 'TL7') {
              // check if the list of improvements is larger than the checkLastIterations
              if (improvementsInLastIterations.length > checkLastIterations) {
                if (improvementsInLastIterations.every(value => !value)) {
                  // Decrease temperature
                  temperature = temperature * alpha;
                  
                  Logger.dev(`New temperature: ${temperature}`);
                }

                // reset the list of improvements
                improvementsInLastIterations = [];
              }
            }
          }


          // if checkpoint for worse solutions accepted is reached
          if (numEvals >= nextEvaluationCheckpoint) {
            // worseSolutionStatistics.push(countWorseSolutionsAccepted);

            // calculate the ratio
            const ratio = countWorseSolutionsAccepted / countWorseSolutions;

            // push the ratio
            worseSolutionStatistics.push(ratio);

            currentRatioStatistics.push({
              x: numEvals,
              y: globals.currentRatio
            });

            // reset the number of worse solutions accepted and the number of worse solutions
            countWorseSolutionsAccepted = 0;
            countWorseSolutions = 0;

            // increase the checkpoint
            nextEvaluationCheckpoint += Math.ceil(0.01 * this.args.evals);
          }

          
          
          const indexGood = Number(meanrawA > meanrawB);
          const indexBad = 1 - indexGood;
          globals.currentRatio = meanrawCheck / Math.min(meanrawB, meanrawA);

          const goodChunks = analyseResult.chunks[indexGood];
          const badChunks = analyseResult.chunks[indexBad];

          ratioString = globals.currentRatio /*aka: new ratio*/
            .toFixed(4);

          per_second_counter++;

          if (Date.now() - time > 1000) {
            time = Date.now();
            show_per_second = (per_second_counter + "/s").padStart(6);
            per_second_counter = 0;
          }


          logMutation({ choice, kept, numEvals });


          if (numEvals % PRINT_EVERY == 0) {
            // print every 10th eval
            // a line every 5% (also to logfile) also write the asm when
            const writeout = numEvals % (this.args.evals / LOG_EVERY) === 0;

            const statusline = genStatusLine({
              ...this.args,
              analyseResult,
              badChunks,
              batchSize,
              choice,
              goodChunks,
              indexBad,
              indexGood,
              kept,
              no_of_instructions: this.no_of_instructions,
              numEvals,
              ratioString,
              show_per_second,
              stacklength,
              symbolname: this.symbolname,
              writeout,
            });
            process.stdout.write(statusline);

            globals.convergence.push(ratioString);
          }

          // Increase  Number of evaluations taken.
          numEvals++;

          if (numEvals >= this.args.evals) {
            // DONE WITH OPTIMISING WRITE EVERYTHING TO DISK AND EXIT.
            globals.time.generateCryptopt =
              (Date.now() - optimistaionStartDate) / 1000 - globals.time.validate;
            clearInterval(intervalHandle);
 
            Logger.log("writing current asm");
            const elapsed = Date.now() - optimistaionStartDate;
            const paddedSeed = padSeed(Paul.initialSeed);

            const statistics = genStatistics({
              paddedSeed,
              ratioString,
              evals: this.args.evals,
              elapsed,
              batchSize,
              numBatches,
              acc: accumulatedTimeSpentByMeasuring,
              numRevert: this.numRevert,
              numMut: this.numMut,
              counter: this.measuresuite.timer,
              framePointer: this.args.framePointer,
              memoryConstraints: this.args.memoryConstraints,
              cyclegoal: this.args.cyclegoal,
            });
            Logger.log(statistics);

            const [asmFile, mutationsCsvFile] = generateResultFilename(
              { ...this.args, symbolname: this.symbolname },
              [`_ratio${ratioString.replace(".", "")}.asm`, `.csv`],
            );

            // write best found solution with headers
            // flip, because we want the last accepted, not the last mutated.
            const flipped = toggleFUNCTIONS(currentNameOfTheFunctionThatHasTheMutation);

            writeString(
              asmFile,
              ["SECTION .text", `\tGLOBAL ${this.symbolname}`, `${this.symbolname}:`]
                .concat(this.asmStrings[flipped])
                .concat(statistics)
                .join("\n"),
            );

            // write optimization statistics
            Logger.log(`Worse solution statistics: ${worseSolutionStatistics}`);

            // format timestamp to be used in chart name
            const timestamp = new Date().toISOString().replace(/:/g, '-').replace(/\./g, '-');

            const endTime = new Date();

            const timeDiff: string = this.formatDateDiff(startTime, endTime);

            const myChart = new ChartJsImage();

            const labels = [];
            for (let i = 1; i <= 100; i++) {
              labels.push(Math.ceil(i*0.01*this.args.evals));
            }
            myChart.setChartJsVersion('4.4.0');
            myChart.setFormat('svg');
            myChart.setWidth('1280');
            myChart.setHeight('720');
            myChart.setConfig({
              type: 'line',
              data: {
                labels: labels,
                datasets: [{
                  label: 'Number of worse solutions accepted',
                  data: worseSolutionStatistics,
                  fill: false,
                  type: 'line',
                  yAxisID: 'y',
                  borderColor: '#36a2eb'
                },
                {
                  label: 'Current ratio',
                  data: currentRatioStatistics,
                  fill: false,
                  type: 'scatter',
                  yAxisID: 'y1',
                  borderColor: '#ff9f40'
                }]
              },
              options: {
                stacked: true,
                plugins: {
                  title: {
                    display: true,
                    text: this.args.optimizer === 'SA' ? `Ratio: ${globals.currentRatio} - ${timestamp} Evals: ${this.args.evals} Opt:${this.args.optimizer} ${temperatureLengthType} Seed: ${this.args.seed} Total time: ${timeDiff}` : 
                    `Ratio: ${globals.currentRatio} - ${timestamp} Evals: ${this.args.evals} Opt:${this.args.optimizer} Seed: ${this.args.seed} Total time: ${timeDiff}`
                  },
                  subtitle: {
                    display: true,
                    text: this.args.optimizer === 'SA' ? `Init tmp: ${initialTemperature} Alpha: ${alpha} Threshold (?): ${threshholdOfAcceptedSolutions}` : ''
                  }
                },
                "scales": {
                  // "yAxes": [
                  // {
                  //   "id": "y",
                  //   "type": "linear",
                  //   "display": true,
                  //   "position": "left",
                  //   "suggestedMax": 1,
                  //   "suggestedMin": 0
                  // }, 
                  // {
                  //   "id": "y1",
                  //   "type": "linear",
                  //   "display": true,
                  //   "position": "right",
                  //   "gridLines": {
                  //     "drawOnChartArea": false
                  //   }
                  // }
                  // ]
                  y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    suggestedMin: 0,
                    suggestedMax: 1.0
                  },
                  y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
            
                    // grid line settings
                    grid: {
                      drawOnChartArea: false, // only want the grid lines for one axis to show up
                    },
                    suggestedMin: 0.9,
                    suggestedMax: 1.1
                  },
                }
              }
            });
            let chartPath = '';


            if (this.args.optimizer === "SA") {
              chartPath = `_${timestamp}_${this.args.optimizer}_${temperatureLengthType}_${this.args.seed}_chart_adapttemp_${initialTemperature}_${alpha}_${threshholdOfAcceptedSolutions}.svg`;
            } else if (this.args.optimizer === "LS") {
              chartPath = `_${timestamp}_${this.args.optimizer}_${this.args.seed}_chart.svg`;
            }

            const [chartFile] = generateResultFilename(
              { ...this.args, symbolname: this.symbolname },
              [`${chartPath}`],
            );

            Logger.dev(this.args.logComment);
            if (this.args.logComment === ' run') {
              Logger.dev('will create charts');
              Logger.dev(`chartFile: ${chartFile}`);
              myChart.toFile(chartFile).then(() => {
                console.log('created chart successfully');
              }).catch(e => {
                console.error('Mothertrucking charts...');
                console.error(e);
              }); 
            }
            // print improvement statistics
            // Calculate the average
            let sum = improvements.reduce((a, b) => a + b, 0);
            let avg = sum / improvements.length;

            // Calculate the median
            let sorted = [...improvements].sort((a, b) => a - b);
            let mid = Math.floor(sorted.length / 2);
            let median = sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;

            // Calculate the standard deviation
            let squareDiffs = improvements.map(value => (value - avg) ** 2);
            let avgSquareDiff = squareDiffs.reduce((a, b) => a + b, 0) / squareDiffs.length;
            let stdDev = Math.sqrt(avgSquareDiff);

            Logger.dev(`Improvements Average: ${avg}`);
            Logger.dev(`Improvements Median: ${median}`);
            Logger.dev(`Improvements Standard Deviation: ${stdDev}`);

            // print worsening statistics
            // Calculate the average
            let sumWorsenings = worsenings.reduce((a, b) => a + b, 0);
            let avgWorsenings = sumWorsenings / worsenings.length;

            // Calculate the median
            let sortedWorsenings = [...worsenings].sort((a, b) => a - b);
            let midWorsenings = Math.floor(sortedWorsenings.length / 2);
            let medianWorsenings = sortedWorsenings.length % 2 !== 0 ? sortedWorsenings[midWorsenings] : (sortedWorsenings[midWorsenings - 1] + sortedWorsenings[midWorsenings]) / 2;

            // Calculate the standard deviation
            let squareDiffsWorsenings = worsenings.map(value => (value - avgWorsenings) ** 2);
            let avgSquareDiffWorsenings = squareDiffsWorsenings.reduce((a, b) => a + b, 0) / squareDiffsWorsenings.length;
            let stdDevWorsenings = Math.sqrt(avgSquareDiffWorsenings);

            Logger.dev(`Worsenings Average: ${avgWorsenings}`);
            Logger.dev(`Worsenings Median: ${medianWorsenings}`);
            Logger.dev(`Worsenings Standard Deviation: ${stdDevWorsenings}`);

            if (shouldProof(this.args)) {
              // and proof correct
              const proofCmd = FiatBridge.buildProofCommand(this.args.curve, this.args.method, asmFile);
              Logger.log(`proofing that asm correct with '${proofCmd}'`);
              try {
                const now = Date.now();
                execSync(proofCmd, { shell: "/usr/bin/bash" });
                const timeForValidation = (Date.now() - now) / 1000;
                appendFileSync(asmFile, `\n; validated in ${timeForValidation}s\n`);
                globals.time.validate += timeForValidation;
              } catch (e) {
                console.error(`tried to prove correct. didnt work. I tried ${proofCmd}`);
                errorOut(ERRORS.proofUnsuccessful);
              }
            }
            Logger.log("done with that current price of assembly code.");
            this.cleanLibcheckfunctions();
            const v = this.measuresuite.destroy();
            Logger.log(`Wonderful. Done with my work. Destroyed measuresuite (${v}). Time for lunch.`);

            resolve(0);
          }
        }
      }, 0);
    });
  }

  private formatDateDiff(date1: Date, date2: Date): string {
    const diff = Math.abs(date1.getTime() - date2.getTime());

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
    const minutes = Math.floor((diff / 1000 / 60) % 60);
    const seconds = Math.floor((diff / 1000) % 60);

    return `${days} days, ${hours} hours, ${minutes} minutes, ${seconds} seconds`;
}

  private cleanLibcheckfunctions() {
    if (existsSync(this.libcheckfunctionDirectory)) {
      try {
        Logger.log(`Removing lib check functions in '${this.libcheckfunctionDirectory}'`);
        rmSync(this.libcheckfunctionDirectory, { recursive: true });
        Logger.log(`removed ${this.libcheckfunctionDirectory}`);
      } catch (e) {
        console.error(e);
        throw e;
      }
    }
  }
}
