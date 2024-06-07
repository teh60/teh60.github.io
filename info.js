const fungalComp = Vue.component('fungal-comp', {
    data() {
        return {
            calc: true,
            allowAny: true,
            refresh: 0,
            tooltip: null,
            userInputs: [{
                rawInput: "",
                rawOutput: "",
                // autoInput: "",
                // autoOutput: "",
            }],
            saveInput: []
        }
    },
    mounted() {
        if (this.$refs.tooltip) {
            this.tooltip = Popper.createPopper(this.$refs.slot.$el, this.$refs.tooltip, {
                placement: 'top',
                modifiers: [{ name: 'offset', options: { offset: [0, 35] } }],
            })
        }
        let params = new URLSearchParams(window.location.search)
        // console.log(params)
        if (params.has('i') && params.has('o')) {
            let inputs = params.getAll('i')
            let outputs = params.getAll('o')
            // inputs.forEach((mat,i)=>{
            //     this.userInputs.push({
            //         rawInput: mat,
            //         rawOutput: outputs[i]
            //     })
            // })
            this.userInputs = inputs.map((mat,i) => {
                return {
                rawInput: mat,
                rawOutput: outputs[i]
        }})
        }
    },
    updated() {
        if (this.tooltip) {
            this.tooltip.update()
        }
    },
    beforeDestroy() {
        if (this.tooltip) {
            this.tooltip.destroy()
            this.tooltip = null
        }
    },
    computed: {
        shiftInfo() {
            let inputs = this.userInputs.map((x) => x.rawInput)
            let outputs = this.userInputs.map((x) => x.rawOutput)
            let calculated = []
            let original = []
            let transformed = {}
            let outputsLoop1 = outputs
            
            for (let i = 0; i < outputs.length; i++) {
                let inInd = inputs.lastIndexOf(outputs[i])
                if (inInd < i && inInd > -1) {
                    outputsLoop1[i] = outputs[inInd]
                    inInd = inputs.lastIndexOf(outputsLoop1[i])
                }
                transformed[inputs[i]] = outputs[i]
            }

            for (let i = 0; i < outputs.length; i++) {
                let inInd = inputs.lastIndexOf(outputs[i])
                let inputMat = inputs[i]
                let originalOutput = outputs[i]
                if (inInd < i && inInd > -1) {
                    outputs[i] = outputs[inInd]
                    inInd = inputs.lastIndexOf(outputs[i])
                }
                let secondMat = outputs[i]
                transformed[inputMat] = secondMat
                let thirdMat = false
                
                if (inInd > i) {
                    thirdMat = outputs[inInd]
                    // console.log("less",i,inInd)
                } else if (transformed[secondMat] != secondMat) {
                    thirdMat = transformed[secondMat]
                    // console.log("ineq",i,inInd)
                }
                // console.log({
                //     shiftNumber: i,
                //     inputFoundInOutput: inInd,
                //     inputMaterial: inputMat,
                //     secondMaterial: secondMat,
                //     thirdMaterial: thirdMat,
                //     transformed: JSON.parse(JSON.stringify(transformed))
                // })
                if (secondMat == thirdMat) {
                    thirdMat = false
                }
                // console.log({
                //     midMat: secondMat,
                //     lastMat: thirdMat,
                //     inputMatAtFoundInd: inputs[inInd],
                //     outputMatAtFoundInd: outputs[inInd]
                // })
                let overwrittenShifts = inputs.map((mat, ind) => (mat == inputMat && ind != i) ? ind : -1)
                // console.log(overwrittenShifts)
                overwrittenShifts.forEach((prevInd) => {
                    // console.log(prevInd, i,JSON.stringify(calculated))
                    if (prevInd > -1 && prevInd < calculated.length && !calculated[prevInd].strike) {
                        calculated[prevInd].strike = prevInd < i
                    }
                })
                calculated[i] = {
                    matInput: inputMat,
                    matInputOutput: secondMat,
                    matOutput: thirdMat,
                }
                original[i] = {
                    matInput: inputMat,
                    matInputOutput: originalOutput,
                }
            }
            
            return {
                calculated: calculated,
                original: original,
            }
        }
    },
    methods: {
        addInput(i) {
            this.userInputs.push({
                rawInput: "",
                rawOutput: "",
            })
            this.$nextTick(() => {
                // this.$nextTick(() => {
                setTimeout(() => {
                    this.$refs.input[i+1].focus()
                }, 300)
                // })
            })
            this.refreshTooltip()
        },
        removeInput(i) {
            this.userInputs.splice(i, 1)
            this.refreshTooltip()
        },
        shiftInputUp(i) {
            this.userInputs[i] = this.userInputs.splice(i - 1, 1, this.userInputs[i])[0]
        },
        shiftInputDown(i) {
            this.userInputs[i] = this.userInputs.splice(i + 1, 1, this.userInputs[i])[0]
        },
        // super jank solution to refresh tooltip positions on data changes
        refreshTooltip() {
            this.saveInput = this.userInputs
            this.userInputs = []
            this.$nextTick(() => {
                this.userInputs = this.saveInput
            })
        },
        getLink() {
            let searchURL = new URL(window.location)
            let uniqueInputs = this.userInputs.map((shift) => ['i',encodeURIComponent(shift.rawInput)])
            let uniqueOutputs = this.userInputs.map((shift) => ['o',encodeURIComponent(shift.rawOutput)])
            searchURL.search = new URLSearchParams(uniqueInputs.concat(uniqueOutputs))
            window.history.replaceState({},'',searchURL)
            // console.log(searchURL.search)
        },
    },
    props: ['shifts', 'timer'],
    template: `<div class="shifts-page">
        <div class="shifts-io">
            <p>Instructions:</p>
            <ul>
                <li>first input is input material, second input is output material</li>
                <li>Tab and Shift Tab cycles to next and previous material input</li>
                <li>When on output material hitting enter adds a new row (shift)</li>
                <li> + , - , &uarr; , and &darr; are all self explanatory</li>
                <li>"Update Link" updates browser URL so you can share configured shifts</li>
            </ul>
            <v-switch v-model="allowAny" title="Allow any material name"></v-switch>
            <div class="button link" @click="getLink" ><u>Update Link</u></div>
            <div class="userShift" v-for="(field, i) in userInputs" :key="i">
                <input type="text" v-model="field.rawInput" ref="input"/>
                <input type="text" v-model="field.rawOutput" @keyup.enter="addInput(i)"/>
                <!-- <material-list v-model="field.autoInput"></material-list>
                <material-list v-model="field.autoOutput"></material-list> -->
                <div class="button" @click="addInput(i)" v-if="i == userInputs.length - 1">+</div>
                <div class="button" @click="removeInput(i)" v-if="userInputs.length > 1">-</div>
                <div class="button" @click="shiftInputUp(i)" v-if="i != 0">&uarr;</div>
                <div class="button" @click="shiftInputDown(i)" v-if="i != userInputs.length - 1">&darr;</div>
            </div>
        </div>
        <div class="shifts-header">
            <p><u>Shifts:</u></p>
            <v-switch ref="slot" v-model="calc" title="Show Broken Chains/Overwrites"></v-switch>
            <div ref="tooltip" class="tooltip fit">
                <p>"Water &#8594; Poison &#8594; Polymorphine" means
                Water is a broken chain, so Water looks and hurts like poison,
                but Water gets stain and ingestion effects from Polymorphine</p>
            </div>
        </div>
        <div v-for="(shift, i) in (calc ? shiftInfo.calculated : shiftInfo.original)" :key="i">
        <p :class="{ strike: shift.strike }">
            <mat-comp v-if="shift.matInput" :material="shift.matInput" side="left" :raw="allowAny"></mat-comp> &#8594; 
            <mat-comp v-if="shift.matInputOutput" :material="shift.matInputOutput" :side="shift.matOutput ? 'top' : 'right'" :raw="allowAny"></mat-comp>
            <span v-if="shift.matOutput"> &#8594; 
                <mat-comp :material="shift.matOutput" side="right" :raw="allowAny"></mat-comp>
            </span>
        </p>
        </div>
    </div>`
    })

const materialComp = Vue.component('mat-comp', {
    data() {
        return {
            tooltip: null,
        }
    },
    mounted() {
        if (this.$refs.tooltip) {
            this.tooltip = Popper.createPopper(this.$refs.slot, this.$refs.tooltip, {
                placement: this.side,
                modifiers: [{ name: 'offset', options: { offset: [0, 5] } }],
            })
        }
    },
    beforeDestroy() {
        if (this.tooltip) {
            this.tooltip.destroy()
            this.tooltip = null
        }
    },
    computed: {
        mat() {
            let both = this.material.split("@")
            return {
                raw: both[0],
                ui: both[1],
            }
        }
    },
    props: ['material', 'side', 'raw'],
    template: `<div class="material tip">
        <span ref="slot">{{ raw ? mat.raw : mat.ui }}</span>
        <div class="tooltip fit" ref="tooltip">
            <p>{{ mat.raw }}</p>
        </div>
    </div>`
})

const vSwitch = Vue.component('v-switch', {
    props: {
        value: { type: Boolean, required: true },
        title: { type: String, required: true },
        disabled: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        return {
            content: false,
        }
    },
    methods: {
        handleInput() {
            this.content = this.$refs.input.checked
            this.$emit('input', this.content)
        },
    },
    template: `<div class="switch-group">
        <label class="switch">
            <input :disabled="disabled" type="checkbox" ref="input" @input="handleInput" :checked="value" tabindex="1"/>
            <span class="slider round"></span>
        </label>
        <span>{{ title }}</span>
    </div>`,
})

const materialList = Vue.component('material-list', {
    props: {
        items: {
            type: Array,
            required: false,
            default: () => [],
        },
        value: String,
    },
    data() {
        return {
            isOpen: false,
            results: [],
            search: '',
            name: '',
            itemI: 0,
            resultInd: 0,
            cursor: {
                start: 0,
                end: 0,
            },
            content: this.value,
        }
    },
    mounted() {
        document.addEventListener('click', this.handleClickOutside)
    },
    destroyed() {
        document.removeEventListener('click', this.handleClickOutside)
    },
    methods: {
        typeChat(event) {
            this.$emit('input', this.content)
            const cursor = event.target.selectionStart
            this.cursor.end = this.search.length
            this.items.forEach((data, i) => {
                if ([event.key, this.search.charAt(cursor - 1)].includes(data.prefix) && data.names.length > 0) {
                    this.isOpen = true
                    this.cursor.start = cursor - 1
                    this.itemI = i
                }
            })
            if ([" ", "Escape"].includes(event.key)) {
                this.exitMention()
            }
            if (this.isOpen) {
                this.name = this.search.substring(this.cursor.start, this.cursor.end + 1)
                if (this.name.indexOf(" ") > -1) {
                    this.name = this.name.split(" ")[0]
                }
                this.filterResults()
                if (this.search.indexOf(this.items[this.itemI].prefix) < 0) {
                    this.exitMention()
                }
                if (event.key == "Tab") {
                    if (this.search.indexOf(this.items[this.itemI].prefix) > -1) {
                        this.mentionReplace(this.results[this.resultInd])
                        this.exitMention()
                    }
                }
            }
        },
        down() {
            if (this.resultInd < this.results.length - 1) {
                this.resultInd++
                this.scrollToSelected()
            }
        },
        up() {
            if (this.resultInd > 0) {
                this.resultInd--
                this.scrollToSelected()
            }
        },
        tab(event) {
            if (this.isOpen) {
                event.preventDefault()
            }
        },
        scrollToSelected() {
            this.$refs.results[this.resultInd].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
        },
        clickItem(result) {
            this.mentionReplace(result)
            this.$refs.inField.focus()
            this.exitMention()
        },
        clickElse(event) {
            if (!this.$el.contains(event.target)) {
                this.exitMention()
            }
        },
        filterResults() {
            this.results = this.items[this.itemI].names.filter((item) => {
                return item.toLowerCase().indexOf(this.name.toLowerCase()) > -1
            })
        },
        exitMention() {
            this.isOpen = false
            this.resultInd = 0
            this.cursor.start = 0
            this.cursor.end = 0
            this.itemI = 0
        },
        mentionReplace(mention) {
            // console.log(this.search.substring(this.cursor.start))
            mention += " "
            const replaced = this.search.substring(this.cursor.start)
                .replace(this.name, mention)
                .replace(/\s{2,}/, " ")
            const saved = this.search.substring(0, this.cursor.start)
            const pos = this.cursor.start + mention.length
            this.search = saved + replaced
            this.$nextTick(() => {
                this.$refs.inField.setSelectionRange(pos, pos)
            })
        },
        sendMsg() {
            this.$emit('input', this.search)
            this.search = ''
            this.exitMention()
        },
    },
    template: `<div class="autocomplete">
        <input type="text" v-model="search" placeholder="Send Message"
            ref="inField" @keydown.tab="tab" @keyup="typeChat"
            @keydown.down.prevent="down" @keydown.up.prevent="up"
            @keydown.enter="sendMsg"/>
        <div class="popup">
            <ul v-show="isOpen" class="autocomplete-results" ref="scroll">
                <li v-for="(result, i) in results" :key="i" @click="clickItem(result)"
                    class="autocomplete-result" :class="{ 'is-active': i == resultInd }"
                    ref="results"
                    >{{ result }}</li>
            </ul>
        </div>
    </div>`
})

const app = new Vue({
    render: function (h) {
        return h(fungalComp)
    },
}).$mount('#app')
