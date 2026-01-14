"""
Comprehensive Test Set for Typo Robustness Evaluation (Issue #967)

This script provides a MUCH larger and more diverse test set (100+ samples)
to properly evaluate clean vs typo accuracy.

Usage:
    python comprehensive_test.py --old-model /path/to/old --new-model /path/to/new
"""

import json
import os
import torch
from pathlib import Path
from transformers import AutoModelForSequenceClassification, AutoTokenizer


# COMPREHENSIVE TEST SET: 100+ samples across all categories
# Each entry: (clean_text, typo_text, expected_category)
TEST_SET = [
    # MATH (10 samples)
    ("Calculate the integral of sin(x) from 0 to pi", 
     "Clculate teh intgral of sin(x) fom 0 to pi", "math"),
    ("What is 15% of 200", 
     "Waht is 15% fo 200", "math"),
    ("Solve for x: 2x + 5 = 15", 
     "Slove for x: 2x + 5 = 15", "math"),
    ("Find the derivative of x squared plus 3x", 
     "Fnd teh derivtive of x sqaured plus 3x", "math"),
    ("What is the square root of 144", 
     "Waht is teh squre root of 144", "math"),
    ("Calculate the area of a circle with radius 5", 
     "Calculte teh area of a cicle with raduis 5", "math"),
    ("Simplify the fraction 24/36", 
     "Simpilfy the fracton 24/36", "math"),
    ("What is the value of pi to 5 decimal places", 
     "Waht is teh vlue of pi to 5 decmal palces", "math"),
    ("Solve the quadratic equation x^2 - 5x + 6 = 0", 
     "Slove the quadrtic equaton x^2 - 5x + 6 = 0", "math"),
    ("Find the sum of the first 10 natural numbers", 
     "Fnd the sum of teh frst 10 natrual numbrs", "math"),
    
    # PHYSICS (10 samples)
    ("Explain Newton's laws of motion", 
     "Expalin Newtons laws of motin", "physics"),
    ("What is the speed of light in a vacuum", 
     "Waht is teh sped of ligt in a vacum", "physics"),
    ("Calculate the kinetic energy of a 5kg object moving at 10 m/s", 
     "Calculte teh kinetc enrgy of a 5kg objct movng at 10 m/s", "physics"),
    ("Describe the theory of relativity", 
     "Descrbe teh thery of relativty", "physics"),
    ("What is the relationship between force, mass and acceleration", 
     "Waht is teh relatonship betwn force, mas and acceleraton", "physics"),
    ("Explain the concept of electromagnetic induction", 
     "Expalin teh concpt of electromagntic inducton", "physics"),
    ("What is the difference between potential and kinetic energy", 
     "Waht is teh differnce betwn potental and kinetc enrgy", "physics"),
    ("How does a nuclear reactor work", 
     "How dose a nuclr reactr work", "physics"),
    ("Explain the photoelectric effect", 
     "Expalin teh photoelctric effct", "physics"),
    ("What is quantum entanglement", 
     "Waht is quantm entanglemnt", "physics"),
    
    # CHEMISTRY (10 samples)
    ("What is the pH of hydrochloric acid", 
     "Waht is teh pH of hydrochlric acid", "chemistry"),
    ("Describe the periodic table of elements", 
     "Descirbe the peirodic tabel of elemnts", "chemistry"),
    ("Explain the molecular structure of benzene", 
     "Expalin teh molcular strcture of benzne", "chemistry"),
    ("What is the chemical formula for water", 
     "Waht is teh chemcal fomula for watr", "chemistry"),
    ("Describe the process of oxidation", 
     "Descrbe teh procss of oxidaton", "chemistry"),
    ("What is the difference between ionic and covalent bonds", 
     "Waht is teh differnce betwn ionc and covalnt bonds", "chemistry"),
    ("Explain acid-base reactions", 
     "Expalin acid-bse reactons", "chemistry"),
    ("What is the structure of an atom", 
     "Waht is teh strcture of an atom", "chemistry"),
    ("Describe the properties of noble gases", 
     "Descrbe teh proprties of nobl gases", "chemistry"),
    ("What is the process of electrolysis", 
     "Waht is teh procss of electrolsis", "chemistry"),
    
    # BIOLOGY (10 samples)
    ("How does DNA replication work", 
     "How dose DNA replicaton work", "biology"),
    ("Explain the process of photosynthesis", 
     "Expalin teh procss of photosynthsis", "biology"),
    ("What is the structure of a cell membrane", 
     "Waht is teh strcture of a cel membane", "biology"),
    ("Describe the theory of evolution", 
     "Descrbe teh thery of evoluton", "biology"),
    ("How does protein synthesis occur", 
     "How dose protien synthsis occr", "biology"),
    ("What is the function of mitochondria", 
     "Waht is teh functon of mitochnodria", "biology"),
    ("Explain how genes are inherited", 
     "Expalin how gnes are inheritd", "biology"),
    ("What is the role of enzymes in digestion", 
     "Waht is teh role of enzmes in digeston", "biology"),
    ("Describe the human immune system", 
     "Descrbe teh hman immue systm", "biology"),
    ("How does natural selection work", 
     "How dose natral selecton work", "biology"),
    
    # COMPUTER SCIENCE (10 samples)
    ("Explain how binary search works", 
     "Expalin how bianry serach wroks", "computer science"),
    ("What is the difference between stack and queue", 
     "Waht is teh differnce betwn stack and queu", "computer science"),
    ("Describe the concept of object-oriented programming", 
     "Descrbe teh concpt of objct-orientd programing", "computer science"),
    ("How does a hash table work", 
     "How dose a hsh tabel work", "computer science"),
    ("Explain the time complexity of quicksort", 
     "Expalin teh time complxity of quicksrt", "computer science"),
    ("What is recursion in programming", 
     "Waht is recurson in programing", "computer science"),
    ("Describe the TCP/IP protocol", 
     "Descrbe teh TCP/IP protocl", "computer science"),
    ("How does machine learning work", 
     "How dose machne learnng work", "computer science"),
    ("What is the difference between SQL and NoSQL databases", 
     "Waht is teh differnce betwn SQL and NoSQL databses", "computer science"),
    ("Explain the concept of big O notation", 
     "Expalin teh concpt of big O notaton", "computer science"),
    
    # HISTORY (10 samples)
    ("When did World War 2 end", 
     "Wehn did Wrold War 2 end", "history"),
    ("Who was the first president of the United States", 
     "Who ws teh frst presidnt of the Untied States", "history"),
    ("Describe the causes of the French Revolution", 
     "Descrbe teh cuases of the Frnech Revoluton", "history"),
    ("When was the Declaration of Independence signed", 
     "Wehn was teh Declaraton of Indpendence signd", "history"),
    ("Who discovered America", 
     "Who discovred Amrica", "history"),
    ("What was the Renaissance period", 
     "Waht was teh Renaissanc peroid", "history"),
    ("Describe the Industrial Revolution", 
     "Descrbe teh Industral Revoluton", "history"),
    ("When did the Roman Empire fall", 
     "Wehn did teh Romn Empire fal", "history"),
    ("Who was Alexander the Great", 
     "Who ws Alexandr teh Great", "history"),
    ("What caused the Cold War", 
     "Waht cuased teh Cold War", "history"),
    
    # ECONOMICS (8 samples)
    ("Explain the law of supply and demand", 
     "Expalin teh law of suply and demnd", "economics"),
    ("What is inflation and what causes it", 
     "Waht is inflaton and waht cuases it", "economics"),
    ("Describe the difference between GDP and GNP", 
     "Descrbe teh differnce betwn GDP and GNP", "economics"),
    ("How do interest rates affect the economy", 
     "How do intrest rates affct teh econmy", "economics"),
    ("What is monetary policy", 
     "Waht is monetry polcy", "economics"),
    ("Explain the concept of market equilibrium", 
     "Expalin teh concpt of markt equilibrum", "economics"),
    ("What is the role of central banks", 
     "Waht is teh role of centrl banks", "economics"),
    ("Describe different types of market structures", 
     "Descrbe diffrent typs of markt structres", "economics"),
    
    # PSYCHOLOGY (8 samples)
    ("What is cognitive behavioral therapy", 
     "Waht is cogntive behavoral therpy", "psychology"),
    ("Explain Maslow's hierarchy of needs", 
     "Expalin Maslows hierarcy of neds", "psychology"),
    ("What is the difference between classical and operant conditioning", 
     "Waht is teh differnce betwn clasical and opernt conditionng", "psychology"),
    ("Describe the stages of cognitive development", 
     "Descrbe teh stags of cogntive developmnt", "psychology"),
    ("What is confirmation bias", 
     "Waht is confirmaton bias", "psychology"),
    ("Explain the concept of emotional intelligence", 
     "Expalin teh concpt of emotonal intellignce", "psychology"),
    ("What is the role of dopamine in the brain", 
     "Waht is teh role of dopamne in teh brain", "psychology"),
    ("Describe different types of memory", 
     "Descrbe diffrent typs of memroy", "psychology"),
    
    # PHILOSOPHY (8 samples)
    ("What is the trolley problem", 
     "Waht is teh troley problm", "philosophy"),
    ("Explain Kant's categorical imperative", 
     "Expalin Kants categorcal imperatve", "philosophy"),
    ("What is the difference between ethics and morality", 
     "Waht is teh differnce betwn ethcs and moraliy", "philosophy"),
    ("Describe Plato's theory of forms", 
     "Descrbe Platos thery of froms", "philosophy"),
    ("What is existentialism", 
     "Waht is existentalsm", "philosophy"),
    ("Explain the concept of free will", 
     "Expalin teh concpt of fre will", "philosophy"),
    ("What is epistemology", 
     "Waht is epistmology", "philosophy"),
    ("Describe the mind-body problem", 
     "Descrbe teh mind-bdy problm", "philosophy"),
    
    # LAW (8 samples)
    ("What is the difference between civil and criminal law", 
     "Waht is teh differnce betwn civil and crimnl law", "law"),
    ("Explain the concept of due process", 
     "Expalin teh concpt of due procss", "law"),
    ("What are constitutional rights", 
     "Waht are constitutonal rghts", "law"),
    ("Describe the role of the Supreme Court", 
     "Descrbe teh role of teh Suprme Court", "law"),
    ("What is intellectual property law", 
     "Waht is intellectul proprty law", "law"),
    ("Explain the concept of precedent in law", 
     "Expalin teh concpt of precednt in law", "law"),
    ("What is the difference between a felony and misdemeanor", 
     "Waht is teh differnce betwn a felny and misdmeanor", "law"),
    ("Describe contract law basics", 
     "Descrbe contrct law bascs", "law"),
    
    # BUSINESS (8 samples)
    ("What is the difference between B2B and B2C", 
     "Waht is teh differnce betwn B2B and B2C", "business"),
    ("Explain the concept of market segmentation", 
     "Expalin teh concpt of markt segmentatn", "business"),
    ("What is a SWOT analysis", 
     "Waht is a SWOT anlysis", "business"),
    ("Describe different types of business structures", 
     "Descrbe diffrent typs of busines structres", "business"),
    ("What is supply chain management", 
     "Waht is suply chain managemnt", "business"),
    ("Explain the concept of ROI", 
     "Expalin teh concpt of ROI", "business"),
    ("What is corporate governance", 
     "Waht is corprate governnce", "business"),
    ("Describe the product life cycle", 
     "Descrbe teh prodct life cylce", "business"),
]


def load_model(model_path: str):
    """Load model and tokenizer from path."""
    # Convert to absolute path for local files
    model_path = os.path.abspath(model_path)
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model path does not exist: {model_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)
    model.eval()
    
    # Load labels
    label_file = os.path.join(model_path, "category_mapping.json")
    if not os.path.exists(label_file):
        label_file = os.path.join(model_path, "label_mapping.json")
    
    if os.path.exists(label_file):
        with open(label_file) as f:
            labels = json.load(f)
            if "idx_to_category" in labels:
                idx_to_label = {int(k): v for k, v in labels["idx_to_category"].items()}
            elif "idx_to_label" in labels:
                idx_to_label = {int(k): v for k, v in labels["idx_to_label"].items()}
            else:
                idx_to_label = model.config.id2label
    else:
        idx_to_label = model.config.id2label
    
    return model, tokenizer, idx_to_label


def predict(model, tokenizer, idx_to_label, text: str):
    """Get prediction for text."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        conf, idx = torch.max(probs, dim=-1)
    return idx_to_label.get(idx.item(), "unknown"), conf.item()


def evaluate_model(model, tokenizer, idx_to_label, test_set):
    """Evaluate model on test set."""
    clean_correct = 0
    typo_correct = 0
    total = len(test_set)
    
    clean_confidences = []
    typo_confidences = []
    
    for clean_text, typo_text, expected in test_set:
        # Clean prediction
        clean_pred, clean_conf = predict(model, tokenizer, idx_to_label, clean_text)
        clean_confidences.append(clean_conf)
        if clean_pred == expected:
            clean_correct += 1
        
        # Typo prediction
        typo_pred, typo_conf = predict(model, tokenizer, idx_to_label, typo_text)
        typo_confidences.append(typo_conf)
        if typo_pred == expected:
            typo_correct += 1
    
    return {
        "clean_accuracy": clean_correct / total * 100,
        "typo_accuracy": typo_correct / total * 100,
        "clean_correct": clean_correct,
        "typo_correct": typo_correct,
        "total": total,
        "avg_clean_conf": sum(clean_confidences) / len(clean_confidences),
        "avg_typo_conf": sum(typo_confidences) / len(typo_confidences),
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Typo Robustness Test")
    parser.add_argument("--old-model", required=True, help="Path to old (deployed) model")
    parser.add_argument("--new-model", required=True, help="Path to new (trained) model")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("COMPREHENSIVE TYPO ROBUSTNESS TEST")
    print(f"Test set size: {len(TEST_SET)} samples")
    print("=" * 80)
    
    # Load models
    print("\nLoading models...")
    old_model, old_tok, old_labels = load_model(args.old_model)
    new_model, new_tok, new_labels = load_model(args.new_model)
    
    # Evaluate
    print("Evaluating old model...")
    old_results = evaluate_model(old_model, old_tok, old_labels, TEST_SET)
    
    print("Evaluating new model...")
    new_results = evaluate_model(new_model, new_tok, new_labels, TEST_SET)
    
    # Print results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    print(f"\n{'Metric':<25} {'Old Model':<15} {'New Model':<15} {'Delta':<10}")
    print("-" * 65)
    
    clean_delta = new_results["clean_accuracy"] - old_results["clean_accuracy"]
    typo_delta = new_results["typo_accuracy"] - old_results["typo_accuracy"]
    
    print(f"{'Clean Accuracy':<25} {old_results['clean_accuracy']:.1f}%{'':<10} {new_results['clean_accuracy']:.1f}%{'':<10} {clean_delta:+.1f}%")
    print(f"{'Typo Accuracy':<25} {old_results['typo_accuracy']:.1f}%{'':<10} {new_results['typo_accuracy']:.1f}%{'':<10} {typo_delta:+.1f}%")
    print(f"{'Avg Clean Confidence':<25} {old_results['avg_clean_conf']:.3f}{'':<12} {new_results['avg_clean_conf']:.3f}")
    print(f"{'Avg Typo Confidence':<25} {old_results['avg_typo_conf']:.3f}{'':<12} {new_results['avg_typo_conf']:.3f}")
    
    print(f"\nSamples: {old_results['total']}")
    print(f"Old: {old_results['clean_correct']}/{old_results['total']} clean, {old_results['typo_correct']}/{old_results['total']} typo")
    print(f"New: {new_results['clean_correct']}/{new_results['total']} clean, {new_results['typo_correct']}/{new_results['total']} typo")
    
    # Recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    if typo_delta > 5 and clean_delta >= -2:
        print("SUCCESS: Significant typo improvement with minimal clean regression")
        print("READY FOR DEPLOYMENT")
    elif typo_delta > 10 and clean_delta >= -5:
        print("GOOD: Strong typo improvement with acceptable clean regression")
        print("CONSIDER DEPLOYMENT with monitoring")
    elif clean_delta < -10:
        print("WARNING: Significant clean accuracy regression")
        print("DO NOT DEPLOY - need to improve training")
    elif typo_delta <= 0:
        print("WARNING: No typo improvement")
        print("NEED DIFFERENT APPROACH")
    else:
        print("MARGINAL: Some improvement but not meeting targets")
        print("CONTINUE EXPERIMENTING")


if __name__ == "__main__":
    main()

